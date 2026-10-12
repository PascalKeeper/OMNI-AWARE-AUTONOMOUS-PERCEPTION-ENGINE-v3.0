"""Tests for the integrated v3.1 pipeline."""
import sys
sys.path.insert(0, "../src")

import numpy as np
from integrated_pipeline import OmniAwareEngine


def test_engine_runs():
    engine = OmniAwareEngine(seed=0)
    rng = np.random.default_rng(0)
    img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
    r = engine.process_frame(img, {"grip": 0.9, "wetness": 0.1})
    assert r["frame"] == 1
    assert "elapsed_ms" in r
    assert "hazards_detected" in r
    assert "braking" in r
    assert "advisories" in r


def test_traction_reduces_speed():
    engine = OmniAwareEngine(seed=1)
    rng = np.random.default_rng(1)
    img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
    # dry traction
    r1 = engine.process_frame(img, {"grip": 0.9, "wetness": 0.1})
    # low traction
    r2 = engine.process_frame(img, {"grip": 0.3, "wetness": 0.9})
    if r1["advisories"] and r2["advisories"]:
        assert r2["advisories"][0]["recommended_speed_kmh"] <= r1["advisories"][0]["recommended_speed_kmh"]


def test_wet_traction_flag():
    engine = OmniAwareEngine(seed=2)
    rng = np.random.default_rng(2)
    img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
    r = engine.process_frame(img, {"grip": 0.3, "wetness": 0.9})
    for a in r["advisories"]:
        assert "traction_grip" in a
        assert a["traction_grip"] == 0.3


if __name__ == "__main__":
    test_engine_runs()
    test_traction_reduces_speed()
    test_wet_traction_flag()
    print("All integrated pipeline tests passed.")