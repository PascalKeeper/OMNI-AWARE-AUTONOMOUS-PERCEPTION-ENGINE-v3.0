"""Tests for the performance benchmark."""
import sys
sys.path.insert(0, "../src")

from benchmark_perf import benchmark, profile_components


def test_benchmark_runs():
    r = benchmark(n_frames=50, seed=0)
    assert r["frames"] == 50
    assert r["mean_fps"] > 0
    assert r["median_fps"] > 0
    assert r["p99_fps"] > 0
    assert r["max_fps"] >= r["mean_fps"]


def test_profile_components():
    r = profile_components(seed=0)
    assert r["filter_ms"] > 0
    assert r["total_ms"] > 0
    assert r["theoretical_fps"] > 0
    # filter should be the dominant cost
    assert r["filter_pct"] > 30


def test_fps_below_422():
    """The real pipeline cannot hit 422 FPS on CPU Python."""
    r = benchmark(n_frames=100, seed=1)
    assert r["mean_fps"] < 422
    assert r["max_fps"] < 422


if __name__ == "__main__":
    test_benchmark_runs()
    test_profile_components()
    test_fps_below_422()
    print("All benchmark perf tests passed.")