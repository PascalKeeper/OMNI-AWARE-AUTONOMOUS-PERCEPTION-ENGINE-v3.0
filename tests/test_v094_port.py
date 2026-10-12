"""Tests for the v0.9.4 port: Kalman fusion + BEV renderer."""
import sys
sys.path.insert(0, "../src")

from kalman_fusion import fuse_entity, fuse_frame, BASE_CONFIDENCE, LIDAR_BOOST, CAMERA_BOOST
from bev_renderer import to_screen, entity_box, entity_color, M_TO_PX


def test_base_confidence():
    e = fuse_entity({"type": "car", "x": 0, "y": 50})
    assert abs(e["confidence"] - (BASE_CONFIDENCE + LIDAR_BOOST + CAMERA_BOOST)) < 1e-9


def test_range_penalty():
    e = fuse_entity({"type": "car", "x": 0, "y": 120})
    assert e["confidence"] < BASE_CONFIDENCE + LIDAR_BOOST + CAMERA_BOOST


def test_confidence_capped():
    e = fuse_entity({"type": "car", "x": 0, "y": 10})
    assert e["confidence"] <= 0.999


def test_fuse_frame_filters():
    ents = [{"type": "car", "x": 0, "y": 50}, {"type": "car", "x": 0, "y": 200}]
    fused = fuse_frame(ents)
    assert len(fused) == 1
    assert fused[0]["y"] == 50


def test_to_screen_center():
    sx, sy = to_screen(0, 0)
    assert sx == 400  # center of 800px canvas


def test_entity_box_size():
    e = {"type": "car", "x": 0, "y": 50, "width": 2.0, "length": 4.5}
    b = entity_box(e)
    assert b["w"] == 2.0 * M_TO_PX * 4
    assert b["h"] == 4.5 * M_TO_PX


def test_entity_colors():
    assert entity_color({"type": "car"}) == "#10b981"
    assert entity_color({"type": "truck"}) == "#eab308"
    assert entity_color({"type": "pedestrian"}) == "#ef4444"


if __name__ == "__main__":
    test_base_confidence()
    test_range_penalty()
    test_confidence_capped()
    test_fuse_frame_filters()
    test_to_screen_center()
    test_entity_box_size()
    test_entity_colors()
    print("All v0.9.4 port tests passed.")