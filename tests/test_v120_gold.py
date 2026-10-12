"""Tests for the v1.2.0-GOLD port: spectrum lock, heartbeat, sensor ranges."""
import sys
sys.path.insert(0, "../src")

from spectrum_lock import apply_spectrum_lock, RED_LOCK, GREEN_LOCK, BLUE_LOCK
from heartbeat import update_heartbeat


def test_spectrum_lock_weights():
    assert RED_LOCK == 0.70
    assert GREEN_LOCK == 0.70
    assert BLUE_LOCK == 0.07


def test_spectrum_lock_pixel():
    r, g, b = apply_spectrum_lock(1.0, 1.0, 1.0)
    assert abs(r - 0.70) < 1e-9
    assert abs(g - 0.70) < 1e-9
    assert abs(b - 0.07) < 1e-9


def test_spectrum_lock_frame():
    from spectrum_lock import apply_spectrum_lock_frame
    frame = [(1.0, 0.5, 0.25)]
    out = apply_spectrum_lock_frame(frame)
    assert abs(out[0][0] - 0.70) < 1e-9
    assert abs(out[0][1] - 0.35) < 1e-9
    assert abs(out[0][2] - 0.0175) < 1e-9


def test_heartbeat_bounds():
    h = {"compute": 42, "heartbeat": 99, "cpu_temp": 45}
    for _ in range(100):
        h = update_heartbeat(h)
        assert 30 <= h["compute"] <= 100
        assert 85 <= h["heartbeat"] <= 100
        assert 40 <= h["cpu_temp"] <= 85


if __name__ == "__main__":
    test_spectrum_lock_weights()
    test_spectrum_lock_pixel()
    test_spectrum_lock_frame()
    test_heartbeat_bounds()
    print("All v1.2.0-GOLD port tests passed.")