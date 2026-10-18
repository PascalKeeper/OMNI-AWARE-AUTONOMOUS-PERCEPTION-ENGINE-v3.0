"""Tests for Fast BEV lookup table."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from fast_bev import FastBevLookup

def test_center_projects_near_zero_lateral():
    bev = FastBevLookup(image_w=640, image_h=480)
    # Bottom-center of image should be near, lateral ~0
    pt = bev.project(320, 470)
    assert pt is not None
    x, y = pt
    assert x > 0
    assert abs(y) < 2.0

def test_edge_has_lateral_offset():
    bev = FastBevLookup(image_w=640, image_h=480)
    left = bev.project(0, 240)
    right = bev.project(639, 240)
    assert left is not None and right is not None
    assert left[1] < 0
    assert right[1] > 0

def test_lookup_is_o1():
    bev = FastBevLookup()
    # Just confirm it returns something for valid coords
    assert bev.project(100, 100) is not None
    assert bev.project(-1, 100) is None
    assert bev.project(100, 9999) is None

def test_table_size_reasonable():
    bev = FastBevLookup(image_w=1280, image_h=720)
    assert 10 < bev.table_size_mb() < 20

def test_fps_estimate_positive():
    bev = FastBevLookup()
    assert bev.fps_estimate(10000) > 0

if __name__ == "__main__":
    for t in [v for k,v in globals().items() if k.startswith("test_")]:
        t()
        print("PASS", t.__name__)
    print("all passed")
