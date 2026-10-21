"""Occluded presence from Wi-Fi beacon density.

A stable RSSI cluster with no camera match promotes on the third frame.
A one-frame spike does not. Changing the MAC does not split the cluster.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pipeline import PerceptionEngine
from temporal_filter import TemporalFilter
from wifi_scan import WifiScanner


PHONE_RSSI = -48.0  # near zone, on a 2 dB bin boundary that is exact


def _phone(mac: str) -> dict:
    return {"mac": mac, "rssi_dbm": PHONE_RSSI}


def _step(scanner, filt, beacons, frame):
    flags = scanner.observe(beacons, visual=False, radar=False)
    points = scanner.track_points(flags)
    labels = ["occluded"] * len(points)
    confirmed = filt.update(points, frame=frame, labels=labels if labels else None)
    return flags, confirmed


def test_phone_behind_van_promotes_on_frame_3():
    scanner = WifiScanner()
    filt = TemporalFilter()
    confirmed = []
    for frame in range(3):
        flags, confirmed = _step(scanner, filt, [_phone("aa:11:22:33:44:55")], frame)
        assert len(flags) == 1
        assert flags[0]["occluded"] is True
        assert flags[0]["delta_db"] > 10.0
        if frame < 2:
            assert confirmed == []
    assert len(confirmed) == 1
    assert confirmed[0].hit_count == 3
    assert confirmed[0].hazard_type == "occluded"


def test_one_frame_spike_never_promotes():
    scanner = WifiScanner()
    filt = TemporalFilter()
    flags, confirmed = _step(scanner, filt, [_phone("aa:11:22:33:44:55")], 0)
    assert len(flags) == 1 and flags[0]["occluded"] is True
    assert confirmed == []
    for frame in range(1, 6):
        flags, confirmed = _step(scanner, filt, [], frame)
        assert flags == []
        assert confirmed == []


def test_mac_randomization_keeps_cluster_for_ten_frames():
    scanner = WifiScanner()
    filt = TemporalFilter()
    first_id = None
    for frame in range(10):
        mac = f"02:00:00:00:00:{frame:02d}"
        flags, confirmed = _step(scanner, filt, [_phone(mac)], frame)
        assert len(flags) == 1
        assert mac not in flags[0]["cluster_id"]
        if first_id is None:
            first_id = flags[0]["cluster_id"]
        else:
            assert flags[0]["cluster_id"] == first_id
        assert len(filt.tracks) == 1
        if frame < 2:
            assert confirmed == []
        else:
            assert len(confirmed) == 1
    assert filt.tracks[0].hit_count == 10
    assert filt.tracks[0].hazard_type == "occluded"


def test_pipeline_logs_wifi_ms_beside_ransac_and_fusion():
    os.environ["OMNI_FILTER_BACKEND"] = "python"
    engine = PerceptionEngine()
    img = np.zeros((24, 32, 3), dtype=np.float32)
    result = engine.process_frame(img, beacons=[_phone("aa:11")])
    assert "wifi_ms" in result
    assert "ransac_ms" in result
    assert "fusion_ms" in result
    assert result["wifi_ms"] >= 0
    assert result["confirmed_hazards"] == []


if __name__ == "__main__":
    test_phone_behind_van_promotes_on_frame_3()
    test_one_frame_spike_never_promotes()
    test_mac_randomization_keeps_cluster_for_ten_frames()
    test_pipeline_logs_wifi_ms_beside_ransac_and_fusion()
    print("wifi occluded-presence tests passed")
