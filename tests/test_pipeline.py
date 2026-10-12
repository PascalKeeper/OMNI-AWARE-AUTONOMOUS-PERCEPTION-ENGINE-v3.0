"""Tests for the OMNI-AWARE v3.0 pipeline."""
import numpy as np
import sys
sys.path.insert(0, "../src")

from rgb_filter import rgb_filter, WEIGHTS
from quadrants import split_quadrants
from ransac import ransac_line
from physics import simulate_falling_object, predict_evasion
from decision import decide, DEFAULT_SCENARIO


def test_filter_weights():
    assert np.array_equal(WEIGHTS, np.array([0.21, 0.70, 0.07]))
    assert abs(WEIGHTS.sum() - 1.0) < 1e-6


def test_filter_shape():
    img = np.random.random((100, 100, 3))
    out = rgb_filter(img)
    assert out.shape == (100, 100)


def test_quadrants_cover_frame():
    g = np.zeros((100, 100))
    qs = split_quadrants(g)
    total = sum(q.size for q in qs.values())
    assert total == 100 * 100


def test_ransac_rejects_boulder():
    rng = np.random.default_rng(0)
    pts = np.column_stack([np.linspace(0, 100, 50), rng.normal(50, 1, 50)])
    pts = np.vstack([pts, [50, 90]])  # boulder
    model, inl, out = ransac_line(pts)
    assert out[-1] == True  # boulder is an outlier


def test_physics_gap():
    t, x_obj, x_truck, gap = simulate_falling_object()
    assert t > 0
    assert gap < 0  # object lands behind the truck


def test_decision_picks_waterfall():
    choice, score, _ = decide(DEFAULT_SCENARIO)
    assert choice == "waterfall"
    assert score > 2.0


if __name__ == "__main__":
    test_filter_weights()
    test_filter_shape()
    test_quadrants_cover_frame()
    test_ransac_rejects_boulder()
    test_physics_gap()
    test_decision_picks_waterfall()
    print("All tests passed.")