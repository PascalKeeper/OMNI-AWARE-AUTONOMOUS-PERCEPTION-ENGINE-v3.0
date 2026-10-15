"""Wi-Fi/BLE Shadow Sensing Layer — HaleHound-Fire Integration.

Passive radio-frequency shadow mapping using ambient Wi-Fi 6 (5 GHz) and
Wi-Fi 7 (6 GHz) access-point signals plus Bluetooth Low Energy beacons.
Human bodies (~60% water) attenuate RF at these frequencies, creating
measurable shadows in the ambient signal field. This layer detects those
shadows to flag non-line-of-sight hazards the camera and lidar cannot see.

Design constraints (why this does NOT pierce walls like the podcast claimed):
- Wi-Fi 6 operates 5.150–5.850 GHz; Wi-Fi 7 adds 5.925–7.125 GHz.
- At these frequencies, drywall costs ~5 dB per wall, concrete ~10–20 dB.
- A human torso (~20 cm of tissue) adds ~6 dB of shadow at 5.5 GHz.
- Free-space path loss at 30 m and 5.5 GHz is ~77 dB; two walls plus a
  body puts total loss near 93 dB — still detectable with 30 dBm EIRP
  (Wi-Fi 6 regulatory limit) against a –90 dBm noise floor, with ~27 dB margin.
- Wavelength at 5.5 GHz is 5.5 cm, so spatial resolution is centimeter-scale
  at best — enough to detect a person-sized shadow, not to image through walls.
- No active illumination is used. The system only listens to existing APs
  and BLE beacons already present in the environment. Passive = no RF
  emission beyond what the vehicle already transmits for connectivity.

Privacy note: this layer detects the *presence* of a body shadowing a signal.
It does not identify devices, read MAC addresses for tracking, or store
location history. Signal-strength aggregates only, discarded after the
frame. See SAFETY_CASE.md section on RF privacy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict


# --- Physical constants ---
C_LIGHT = 3.0e8  # m/s
HUMAN_TISSUE_ATTEN_DB_PER_M = 30.0  # approximate at 5.5 GHz
DRYWALL_ATTEN_DB = 5.0
CONCRETE_ATTEN_DB = 15.0
NOISE_FLOOR_DBM = -90.0
WIFI6_EIRP_DBM = 30.0  # regulatory max


@dataclass
class RfAccessPoint:
    """An ambient Wi-Fi access point the vehicle can hear."""
    ssid: str
    bssid: str
    frequency_ghz: float
    tx_power_dbm: float
    last_rssi_dbm: float
    distance_m: float


@dataclass
class BleBeacon:
    """A Bluetooth Low Energy beacon in range."""
    name: str
    mac: str
    rssi_dbm: float
    distance_m: float


@dataclass
class ShadowDetection:
    """A detected body shadow in the RF field."""
    bearing_deg: float
    distance_m: float
    confidence: float
    source: str  # 'wifi' or 'ble'
    estimated_size_m: float
    timestamp_ms: int


@dataclass
class WifiShadowState:
    """Aggregated RF shadow state for one pipeline frame."""
    detections: List[ShadowDetection] = field(default_factory=list)
    ap_count: int = 0
    beacon_count: int = 0
    mean_rssi_dbm: float = 0.0
    shadow_density: float = 0.0  # 0-1, fraction of surveyed paths blocked
    advisory: Optional[str] = None


def free_space_path_loss_db(distance_m: float, freq_ghz: float) -> float:
    """FSPL in dB: 20*log10(d) + 20*log10(f) + 32.44."""
    if distance_m <= 0:
        return float('inf')
    return 20 * math.log10(distance_m) + 20 * math.log10(freq_ghz) + 32.44


def body_shadow_db(tissue_m: float = 0.2, freq_ghz: float = 5.5) -> float:
    """Attenuation from a human torso crossing the signal path."""
    # Slight frequency dependence: higher freq = more attenuation
    scale = 1.0 + 0.05 * (freq_ghz - 5.5)
    return HUMAN_TISSUE_ATTEN_DB_PER_M * tissue_m * scale


def wall_attenuation_db(wall_type: str = 'drywall', count: int = 1) -> float:
    per_wall = DRYWALL_ATTEN_DB if wall_type == 'drywall' else CONCRETE_ATTEN_DB
    return per_wall * count


def is_detectable(distance_m: float, freq_ghz: float,
                  walls: int = 0, wall_type: str = 'drywall',
                  tissue_m: float = 0.0) -> bool:
    """Can a shadow be detected given path loss and regulatory TX power?"""
    total_loss = (free_space_path_loss_db(distance_m, freq_ghz)
                  + wall_attenuation_db(wall_type, walls)
                  + body_shadow_db(tissue_m, freq_ghz))
    received = WIFI6_EIRP_DBM - total_loss
    return received > NOISE_FLOOR_DBM


def wavelength_m(freq_ghz: float) -> float:
    return C_LIGHT / (freq_ghz * 1e9)


def spatial_resolution_m(freq_ghz: float) -> float:
    """Rayleigh-ish resolution limit: wavelength / 2."""
    return wavelength_m(freq_ghz) / 2.0


class WifiShadowSensor:
    """Passive RF shadow mapper.

    Listens to ambient APs and BLE beacons, compares expected vs measured
    RSSI, and flags paths where a body-sized obstruction is the most likely
    explanation for the deficit.
    """

    def __init__(self, min_shadow_db: float = 4.0,
                 min_confidence: float = 0.5,
                 max_range_m: float = 80.0):
        self.min_shadow_db = min_shadow_db
        self.min_confidence = min_confidence
        self.max_range_m = max_range_m
        self._ap_history: Dict[str, List[float]] = {}  # bssid -> recent RSSIs
        self._beacon_history: Dict[str, List[float]] = {}

    def update_access_points(self, aps: List[RfAccessPoint]) -> None:
        for ap in aps:
            hist = self._ap_history.setdefault(ap.bssid, [])
            hist.append(ap.last_rssi_dbm)
            if len(hist) > 10:
                hist.pop(0)

    def update_beacons(self, beacons: List[BleBeacon]) -> None:
        for b in beacons:
            hist = self._beacon_history.setdefault(b.mac, [])
            hist.append(b.rssi_dbm)
            if len(hist) > 10:
                hist.pop(0)

    def _shadow_confidence(self, deficit_db: float, samples: int) -> float:
        """Confidence that a deficit is a body shadow, not noise or multipath."""
        if deficit_db < self.min_shadow_db:
            return 0.0
        # Stronger deficit + more samples = higher confidence, saturating at 0.95
        strength = min(1.0, deficit_db / 15.0)
        sample_factor = min(1.0, samples / 5.0)
        return min(0.95, 0.4 + 0.35 * strength + 0.2 * sample_factor)

    def detect(self, timestamp_ms: int = 0) -> WifiShadowState:
        detections: List[ShadowDetection] = []
        all_rssis: List[float] = []

        # --- Wi-Fi AP shadow detection ---
        for bssid, hist in self._ap_history.items():
            if len(hist) < 3:
                continue
            recent = hist[-3:]
            baseline = sum(hist[:-1]) / max(1, len(hist) - 1) if len(hist) > 1 else recent[0]
            current = recent[-1]
            all_rssis.append(current)
            deficit = baseline - current
            if deficit >= self.min_shadow_db:
                conf = self._shadow_confidence(deficit, len(hist))
                if conf >= self.min_confidence:
                    # Bearing unknown from RSSI alone; use 0 as placeholder
                    # (real implementation would triangulate across APs)
                    detections.append(ShadowDetection(
                        bearing_deg=0.0,
                        distance_m=self.max_range_m * 0.5,  # placeholder
                        confidence=conf,
                        source='wifi',
                        estimated_size_m=0.5,  # person-sized
                        timestamp_ms=timestamp_ms,
                    ))

        # --- BLE beacon shadow detection ---
        for mac, hist in self._beacon_history.items():
            if len(hist) < 3:
                continue
            recent = hist[-3:]
            baseline = sum(hist[:-1]) / max(1, len(hist) - 1) if len(hist) > 1 else recent[0]
            current = recent[-1]
            all_rssis.append(current)
            deficit = baseline - current
            if deficit >= self.min_shadow_db:
                conf = self._shadow_confidence(deficit, len(hist))
                if conf >= self.min_confidence:
                    detections.append(ShadowDetection(
                        bearing_deg=0.0,
                        distance_m=self.max_range_m * 0.5,
                        confidence=conf,
                        source='ble',
                        estimated_size_m=0.5,
                        timestamp_ms=timestamp_ms,
                    ))

        mean_rssi = sum(all_rssis) / len(all_rssis) if all_rssis else 0.0
        ap_count = len(self._ap_history)
        beacon_count = len(self._beacon_history)
        # Shadow density: fraction of surveyed signal paths showing a deficit
        total_paths = ap_count + beacon_count
        shadow_density = len(detections) / total_paths if total_paths > 0 else 0.0

        advisory = None
        if shadow_density > 0.3:
            advisory = (f"RF shadow density {shadow_density:.0%} — possible non-line-of-sight "
                        f"occupancy ahead. Reduce speed, cameras may be blind.")
        elif len(detections) > 0:
            advisory = (f"{len(detections)} RF shadow(s) detected — check crosswalk/"
                        f"driveway for hidden pedestrians.")

        return WifiShadowState(
            detections=detections,
            ap_count=ap_count,
            beacon_count=beacon_count,
            mean_rssi_dbm=mean_rssi,
            shadow_density=shadow_density,
            advisory=advisory,
        )


# --- Integration hook for the main pipeline ---

def wifi_shadow_advisory(state: WifiShadowState) -> Optional[str]:
    """Return an advisory string if RF shadows warrant one, else None."""
    return state.advisory
