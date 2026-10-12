"""Tests for the Grok API client."""
import sys
sys.path.insert(0, "../src")

import numpy as np
from grok_client import _local_fallback, _encode_frame


def test_local_fallback_no_outliers():
    r = _local_fallback([])
    assert r["hazard_type"] == "none"
    assert r["source"] == "local_fallback"


def test_local_fallback_boulder():
    pts = [[x, y] for y in range(100) for x in range(100)]  # 100x100 cluster
    r = _local_fallback(pts)
    assert r["hazard_type"] == "boulder"
    assert r["threat_level"] == "high"
    assert r["estimated_size_m"] >= 1.0


def test_local_fallback_debris():
    pts = [[10, 10], [11, 12], [12, 11]]
    r = _local_fallback(pts)
    assert r["hazard_type"] == "debris"
    assert r["threat_level"] == "low"


def test_encode_frame():
    g = np.random.random((100, 100))
    b64 = _encode_frame(g)
    assert isinstance(b64, str)
    assert len(b64) > 0


if __name__ == "__main__":
    test_local_fallback_no_outliers()
    test_local_fallback_boulder()
    test_local_fallback_debris()
    test_encode_frame()
    print("All Grok client tests passed.")