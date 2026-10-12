"""Tests for the v1.0.4 port: sensor fusion, predictive braking, AI backdoor."""
import sys
sys.path.insert(0, "../src")

from sensor_fusion import detect_sensors, compute_confidence, fuse_frame
from predictive_braking import check_collision_warning, should_brake, BRAKE_THRESHOLD_M
from ai_copilot import analyze_scene, generate_report
from canvas_renderer import project, entity_color


def test_radar_first():
    assert detect_sensors(200) == []
    assert detect_sensors(140) == ["RADAR"]
    assert detect_sensors(100) == ["RADAR", "CAMERA"]
    assert detect_sensors(50) == ["RADAR", "CAMERA", "LIDAR"]


def test_confidence_climbs():
    c1 = compute_confidence(140, ["RADAR"])
    c3 = compute_confidence(50, ["RADAR", "CAMERA", "LIDAR"])
    assert c3 > c1
    assert c3 <= 0.99


def test_fusion_frame():
    ents = [{"type": "CAR", "x": 0, "z": 60, "width": 2.5, "height": 2}]
    fused = fuse_frame(ents)
    assert fused[0]["detected_by"] == ["RADAR", "CAMERA", "LIDAR"]
    assert fused[0]["confidence"] > 0.5


def test_braking_threshold():
    ents = [{"type": "PEDESTRIAN", "x": 0, "z": 15}]
    assert should_brake(ents) is True
    ents2 = [{"type": "PEDESTRIAN", "x": 0, "z": 25}]
    assert should_brake(ents2) is False
    ents3 = [{"type": "CAR", "x": 50, "z": 10}]
    assert should_brake(ents3) is False  # out of lane


def test_ai_offline_fallback():
    r = analyze_scene({"speed": "72 km/h"})  # no API keys
    assert r["provider"] == "none"
    assert "Offline" in r["text"]


def test_canvas_projection():
    e = {"type": "CAR", "x": 0, "z": 100, "width": 2.5, "height": 2}
    p = project(e)
    assert 350 < p["x"] < 450
    assert p["y"] > 200
    assert p["w"] > 0 and p["h"] > 0


def test_entity_colors():
    assert entity_color({"type": "CAR"}) == "#34d399"
    assert entity_color({"type": "PEDESTRIAN"}) == "#fbbf24"
    assert entity_color({"type": "OBSTACLE"}) == "#f87171"


if __name__ == "__main__":
    test_radar_first()
    test_confidence_climbs()
    test_fusion_frame()
    test_braking_threshold()
    test_ai_offline_fallback()
    test_canvas_projection()
    test_entity_colors()
    print("All v1.0.4 port tests passed.")