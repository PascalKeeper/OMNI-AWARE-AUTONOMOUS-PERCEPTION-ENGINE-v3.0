"""Tests for the real-pipeline simulation."""
import sys
sys.path.insert(0, "../src")

import numpy as np
from real_pipeline_sim import RealPipelineSim


def test_distance_decay():
    sim = RealPipelineSim(seed=0)
    # close object: high detection probability
    gt_close = [{"type": "car", "x": 0, "y": 10, "w": 2, "h": 1.5}]
    # far object: low detection probability
    gt_far = [{"type": "car", "x": 0, "y": 140, "w": 2, "h": 1.5}]
    dets_close = [sim.detect(gt_close) for _ in range(100)]
    dets_far = [sim.detect(gt_far) for _ in range(100)]
    rate_close = sum(1 for d in dets_close if len(d) > 0) / 100
    rate_far = sum(1 for d in dets_far if len(d) > 0) / 100
    assert rate_close > rate_far


def test_false_positive_injection():
    sim = RealPipelineSim(seed=0)
    gt = [{"type": "car", "x": 0, "y": 50, "w": 2, "h": 1.5}]
    fps = 0
    for _ in range(100):
        dets = sim.detect(gt)
        # FP = detection not matching the GT car
        matched = any(abs(d["x"]) < 2 and abs(d["y"] - 50) < 5 for d in dets)
        if len(dets) > 1 or (len(dets) == 1 and not matched):
            # count extra detections beyond the matched one
            extras = len(dets) - (1 if matched else 0)
            fps += extras
    assert fps > 0  # FP injection is happening


def test_color_dependent_miss():
    sim = RealPipelineSim(seed=42)
    gt = [{"type": "pedestrian", "x": 0, "y": 30, "w": 0.5, "h": 1.8}]
    # run many times; some should miss the pedestrian
    misses = 0
    for _ in range(200):
        dets = sim.detect(gt)
        if not any(d["type"] == "pedestrian" for d in dets):
            misses += 1
    assert misses > 0  # color-dependent misses are occurring


def test_evaluate_runs():
    sim = RealPipelineSim(seed=0)
    r = sim.evaluate(n_scenes=2, frames=10)
    assert r["frames"] == 20
    assert 0 <= r["precision"] <= 1
    assert 0 <= r["recall"] <= 1
    assert r["p99_ms"] >= r["p50_ms"]


def test_metrics_worse_than_perfect():
    """Real pipeline should be worse than the perfect simulated detector."""
    sim = RealPipelineSim(seed=0)
    r = sim.evaluate(n_scenes=10, frames=20)
    # recall should be meaningfully below 1.0 due to distance decay + color misses
    assert r["recall"] < 0.95


if __name__ == "__main__":
    test_distance_decay()
    test_false_positive_injection()
    test_color_dependent_miss()
    test_evaluate_runs()
    test_metrics_worse_than_perfect()
    print("All real pipeline sim tests passed.")