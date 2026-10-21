"""Wi-Fi beacon density layer for occluded presence.

Polls nearby beacons about every 0.5 seconds. Identity is the RSSI
pattern and its timing, not the MAC. iOS and Android randomize MACs,
so a phone that keeps the same strength stays one cluster.

Linux polls with nmcli, then pywifi if nmcli is absent. The C++ port
reads `iw` / nl80211 when it is built on Linux. This module also
accepts an injected beacon list so tests do not need a radio.

A cell more than 10 dB above its rolling background, with no camera
match and no radar return, is an occluded presence. The pipeline feeds
that cell to TemporalFilter as a tentative track. Promotion still
takes three consecutive hits.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field

POLL_S = 0.5
SPIKE_DB = 10.0
QUIET_FLOOR_DBM = -85.0
EMA_ALPHA = 0.05

# Forward range used when angle-of-arrival is unavailable.
ZONE_RANGE_M = {"near": 4.0, "mid": 15.0, "far": 40.0}


def zone_for_rssi(rssi_dbm: float) -> str | None:
    if rssi_dbm >= -50.0:
        return "near"
    if rssi_dbm >= -70.0:
        return "mid"
    if rssi_dbm >= -90.0:
        return "far"
    return None


def cluster_id(zone: str, rssi_dbm: float, aoa_deg: float | None = None) -> str:
    """Stable id from zone, a 2 dB RSSI bin, and optional angle. No MAC."""
    rssi_bin = int(round(rssi_dbm / 2.0)) * 2
    if aoa_deg is None:
        return f"{zone}:{rssi_bin}"
    aoa_bin = int(round(aoa_deg / 15.0)) * 15
    return f"{zone}:{rssi_bin}:aoa{aoa_bin}"


def centroid_for(zone: str, aoa_deg: float | None = None) -> tuple[float, float]:
    """Return (x lateral, z forward) meters for a grid cell."""
    z = ZONE_RANGE_M[zone]
    if aoa_deg is None:
        return (0.0, z)
    x = math.sin(math.radians(aoa_deg)) * z
    return (x, z)


@dataclass
class WifiScanner:
    poll_s: float = POLL_S
    spike_db: float = SPIKE_DB
    live: bool = False
    source: callable | None = None
    _ema: dict[str, float] = field(default_factory=dict)
    _last_poll: float = 0.0
    _cached: list[dict] = field(default_factory=list)

    def read_beacons(self, now: float | None = None) -> list[dict]:
        """Return the latest beacon list, polling at most every poll_s."""
        clock = time.monotonic() if now is None else now
        if self._cached and (clock - self._last_poll) < self.poll_s:
            return list(self._cached)
        self._last_poll = clock
        if self.source is not None:
            self._cached = list(self.source())
        elif self.live:
            self._cached = _poll_platform()
        else:
            self._cached = []
        return list(self._cached)

    def observe(
        self,
        beacons: list[dict],
        visual: bool = False,
        radar: bool = False,
        visual_zones: set[str] | None = None,
    ) -> list[dict]:
        """Bin beacons and flag occluded spikes.

        `visual` is a frame-level camera match. `visual_zones` limits
        that match to named zones. Radar does the same for the whole frame.
        """
        by_cell: dict[str, dict] = {}
        for beacon in beacons:
            rssi = float(beacon["rssi_dbm"])
            zone = zone_for_rssi(rssi)
            if zone is None:
                continue
            aoa = beacon.get("aoa_deg")
            cid = cluster_id(zone, rssi, aoa)
            current = by_cell.get(cid)
            if current is None or rssi > current["rssi_dbm"]:
                by_cell[cid] = {
                    "zone": zone,
                    "rssi_dbm": rssi,
                    "aoa_deg": aoa,
                    "cluster_id": cid,
                    "centroid": centroid_for(zone, aoa),
                }
        flagged = []
        for cid, cell in by_cell.items():
            background = self._ema.get(cid, QUIET_FLOOR_DBM)
            delta = cell["rssi_dbm"] - background
            camera_match = visual and (visual_zones is None or cell["zone"] in visual_zones)
            occluded = delta > self.spike_db and not camera_match and not radar
            cell["background_dbm"] = background
            cell["delta_db"] = delta
            cell["occluded"] = occluded
            flagged.append(cell)
            # Slow average so a real presence stays above the floor for
            # several frames instead of becoming the new background at once.
            self._ema[cid] = (1.0 - EMA_ALPHA) * background + EMA_ALPHA * cell["rssi_dbm"]
        return flagged

    def track_points(self, flags: list[dict]) -> list[tuple[float, float]]:
        """Centroids that should enter the temporal filter."""
        return [tuple(flag["centroid"]) for flag in flags if flag["occluded"]]


def _poll_platform() -> list[dict]:
    """Live poll. Linux uses nmcli, then pywifi. Windows uses netsh."""
    if sys.platform.startswith("linux"):
        found = _poll_nmcli()
        if found:
            return found
        return _poll_pywifi()
    if sys.platform.startswith("win"):
        return _poll_netsh()
    return []


def _poll_nmcli() -> list[dict]:
    if shutil.which("nmcli") is None:
        return []
    try:
        proc = subprocess.run(
            ["nmcli", "-t", "-f", "BSSID,SIGNAL,FREQ", "dev", "wifi", "list"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    beacons = []
    for line in proc.stdout.splitlines():
        parts = line.split(":")
        # BSSID itself contains colons, so the tail is signal and freq.
        if len(parts) < 8:
            continue
        signal = parts[-2]
        freq = parts[-1]
        try:
            quality = float(signal)
            mhz = float(freq)
        except ValueError:
            continue
        beacons.append({
            "mac": ":".join(parts[:-2]),
            "rssi_dbm": quality / 2.0 - 100.0,
            "mhz": mhz,
        })
    return beacons


def _poll_pywifi() -> list[dict]:
    try:
        import pywifi
    except ImportError:
        return []
    wifi = pywifi.PyWiFi()
    ifaces = wifi.interfaces()
    if not ifaces:
        return []
    iface = ifaces[0]
    iface.scan()
    time.sleep(POLL_S)
    beacons = []
    for net in iface.scan_results():
        beacons.append({
            "mac": getattr(net, "bssid", ""),
            "rssi_dbm": float(getattr(net, "signal", -100)),
            "mhz": 0.0,
        })
    return beacons


def _poll_netsh() -> list[dict]:
    if shutil.which("netsh") is None:
        return []
    try:
        proc = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    beacons = []
    mac = ""
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("BSSID"):
            mac = stripped.split(":", 1)[-1].strip()
        elif stripped.startswith("Signal") and mac:
            try:
                quality = float(stripped.split(":", 1)[-1].replace("%", "").strip())
            except ValueError:
                continue
            beacons.append({"mac": mac, "rssi_dbm": quality / 2.0 - 100.0, "mhz": 0.0})
            mac = ""
    return beacons
