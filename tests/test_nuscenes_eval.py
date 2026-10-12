"""Tests for the nuScenes evaluation harness."""
import sys
sys.path.insert(0, "../src")

import numpy as np
from nuscenes_eval import NuScenesEval


def test_match_perfect():
    ev = NuScenesEval(seed=0)
    gt = [{"type": "car", "x": 0, "y": 50, "w": 2, "h": 1.5}]
    dets = [{"type": "car", "x": 0.1, "y": 50.1, "w": 2, "h": 1.5, "confidence": 0.9}]
    tp, fp, fn = ev.match(gt, dets)
    assert tp == 1 and fp == 0 and fn == 0


def test_match_false_positive():
    ev = NuScenesEval(seed=0)
    gt = [{"type": "car", "x": 0, "y": 50, "w": 2, "h": 1.5}]
    dets = [gt[0], {"type": "car", "x": 5, "y": 60, "w": 2, "h": 1.5, "confidence": 0.4}]
    tp, fp, fn = ev.match(gt, dets)
    assert tp == 1 and fp == 1 and fn == 0


def test_match_false_negative():
    ev = NuScenesEval(seed=0)
    gt = [{"type": "car", "x": 0, "y": 50, "w": 2, "h": 1.5},
          {"type": "pedestrian", "x": 3, "y": 30, "w": 0.5, "h": 1.8}]
    dets = [{"type": "car", "x": 0.1, "y": 50.1, "w": 2, "h": 1.5, "confidence": 0.9}]
    tp, fp, fn = ev.match(gt, dets)
    assert tp == 1 and fp == 0 and fn == 1


def test_match_type_mismatch():
    ev = NuScenesEval(seed=0)
    gt = [{"type": "car", "x": 0, "y": 50, "w": 2, "h": 1.5}]
    dets = [{"type": "pedestrian", "x": 0.1, "y": 50.1, "w": 0.5, "h": 1.8, "confidence": 0.9}]
    tp, fp, fn = ev.match(gt, dets)
    assert tp == 0  # type mismatch = no match


def test_evaluate_runs():
    ev = NuScenesEval(n_scenes=2, frames_per_scene=10, seed=0)
    result = ev.evaluate()
    assert result["frames"] == 20
    assert result["precision"] >= 0
    assert result["recall"] >= 0
    assert result["f1"] >= 0
    assert result["latency_p50_ms"] >= 0
    assert result["latency_p99_ms"] >= result["latency_p50_ms"]


def test_precision_recall_bounds():
    ev = NuScenesEval(n_scenes=5, frames_per_scene=20, seed=1)
    result = ev.evaluate()
    assert 0 <= result["precision"] <= 1
    assert 0 <= result["recall"] <= 1


if __name__ == "__main__":
    test_match_perfect()
    test_match_false_positive()
    test_match_false_negative()
    test_match_type_mismatch()
    test_evaluate_runs()
    test_precision_recall_bounds()
    print("All nuScenes eval tests passed.")