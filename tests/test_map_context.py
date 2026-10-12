"""Tests for the map-aware prediction layer."""
import sys
sys.path.insert(0, "../src")

from map_context import MapContext, turn_risk, brake_distance, speed_advisory


def test_turn_risk_increases_with_speed():
    r1 = turn_risk(12.0, 40/3.6, 80)
    r2 = turn_risk(12.0, 70/3.6, 80)
    assert r2 > r1


def test_turn_risk_increases_with_curvature():
    r1 = turn_risk(2.0, 40/3.6, 80)
    r2 = turn_risk(12.0, 40/3.6, 80)
    assert r2 > r1


def test_brake_distance():
    # at 30 km/h with 7 m/s^2 decel: v=8.33, d = 69.4/14 = 4.96
    assert abs(brake_distance(30/3.6) - 4.96) < 0.1


def test_speed_advisory_alleyway():
    seg = {"type": "alleyway", "sight_distance_m": 25, "curvature_deg_per_m": 8.0,
           "speed_limit_kmh": 30, "distance_ahead_m": 50}
    adv = speed_advisory(seg, 30/3.6)
    assert adv["recommended_speed_kmh"] <= 30
    assert adv["action"] in ("slow down", "maintain")


def test_map_context_upcoming():
    mc = MapContext()
    mc.advance(150)
    up = mc.upcoming(200)
    types = [s["type"] for s in up]
    assert "right_turn" in types or "alleyway" in types


if __name__ == "__main__":
    test_turn_risk_increases_with_speed()
    test_turn_risk_increases_with_curvature()
    test_brake_distance()
    test_speed_advisory_alleyway()
    test_map_context_upcoming()
    print("All map context tests passed.")