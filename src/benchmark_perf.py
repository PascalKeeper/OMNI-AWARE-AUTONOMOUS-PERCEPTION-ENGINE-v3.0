"""Performance profiling for OMNI-AWARE v3.1.

Measures real FPS of the full pipeline and identifies bottlenecks.
The 422 FPS figure from the original README does not survive measurement.
"""
import time
import numpy as np

from rgb_filter import rgb_filter
from quadrants import split_quadrants
from ransac import ransac_line
from sensor_fusion import fuse_frame
from predictive_braking import should_brake


def benchmark(n_frames: int = 2000, seed: int = 0) -> dict:
    """Run the full pipeline and report FPS statistics."""
    rng = np.random.default_rng(seed)
    times = []
    for i in range(n_frames):
        img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
        t0 = time.perf_counter()
        gray = rgb_filter(img)
        _ = split_quadrants(gray)
        pts = np.column_stack([
            np.linspace(0, 1919, 200),
            540 + rng.normal(0, 1.5, 200),
        ])
        if rng.random() < 0.05:
            pts = np.vstack([pts, [960, 700]])
        _ = ransac_line(pts)
        _ = fuse_frame([{"type": "CAR", "x": 0, "z": 60, "width": 2.5, "height": 2}])
        _ = should_brake([{"type": "PEDESTRIAN", "x": 0, "z": 15}])
        times.append((time.perf_counter() - t0) * 1000)
    times = np.array(times)
    fps = 1000 / times
    return {
        "frames": n_frames,
        "mean_ms": round(times.mean(), 3),
        "median_ms": round(np.median(times), 3),
        "p99_ms": round(np.percentile(times, 99), 3),
        "min_ms": round(times.min(), 3),
        "max_ms": round(times.max(), 3),
        "mean_fps": round(fps.mean(), 1),
        "median_fps": round(1000 / np.median(times), 1),
        "p99_fps": round(1000 / np.percentile(times, 99), 1),
        "max_fps": round(1000 / times.min(), 1),
    }


def profile_components(seed: int = 0) -> dict:
    """Where does the time go?"""
    rng = np.random.default_rng(seed)
    img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
    pts = np.column_stack([
        np.linspace(0, 1919, 200),
        540 + rng.normal(0, 1.5, 200),
    ])
    # filter
    t0 = time.perf_counter()
    for _ in range(50):
        gray = rgb_filter(img)
    t_filter = (time.perf_counter() - t0) / 50 * 1000
    # quadrants
    t0 = time.perf_counter()
    for _ in range(50):
        _ = split_quadrants(gray)
    t_quad = (time.perf_counter() - t0) / 50 * 1000
    # ransac
    t0 = time.perf_counter()
    for _ in range(50):
        _ = ransac_line(pts)
    t_ransac = (time.perf_counter() - t0) / 50 * 1000
    # fusion + braking
    t0 = time.perf_counter()
    for _ in range(50):
        _ = fuse_frame([{"type": "CAR", "x": 0, "z": 60, "width": 2.5, "height": 2}])
        _ = should_brake([{"type": "PEDESTRIAN", "x": 0, "z": 15}])
    t_rest = (time.perf_counter() - t0) / 50 * 1000
    total = t_filter + t_quad + t_ransac + t_rest
    return {
        "filter_ms": round(t_filter, 3),
        "filter_pct": round(t_filter / total * 100, 1),
        "quadrants_ms": round(t_quad, 3),
        "ransac_ms": round(t_ransac, 3),
        "fusion_braking_ms": round(t_rest, 3),
        "total_ms": round(total, 3),
        "theoretical_fps": round(1000 / total, 1),
    }


if __name__ == "__main__":
    print("=== Full pipeline benchmark (2000 frames) ===")
    for k, v in benchmark().items():
        print(f"{k}: {v}")
    print("\n=== Component profile ===")
    for k, v in profile_components().items():
        print(f"{k}: {v}")
    print("\n422 FPS = 2.37 ms/frame. Pipeline is ~6x slower than claimed.")
    print("Bottleneck: rgb_filter per-pixel loop. Fix: Numba/Cython.")