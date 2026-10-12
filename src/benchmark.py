"""Benchmark: filter + quadrants + RANSAC pipeline."""
import time
import numpy as np
from rgb_filter import rgb_filter
from quadrants import split_quadrants
from ransac import ransac_line


def run_benchmark(n_frames: int = 2000, seed: int = 0):
    rng = np.random.default_rng(seed)
    img = rng.random((1080, 1920, 3)).astype(np.float32)
    t0 = time.perf_counter()
    for _ in range(n_frames):
        g = rgb_filter(img)
        _ = split_quadrants(g)
        pts = np.column_stack([
            np.linspace(0, 1919, 200),
            540 + rng.normal(0, 1.5, 200),
        ])
        pts = np.vstack([pts, [960, 700]])  # boulder outlier
        ransac_line(pts)
    elapsed = time.perf_counter() - t0
    fps = n_frames / elapsed
    return fps, 1000 * elapsed / n_frames


if __name__ == "__main__":
    fps, ms = run_benchmark()
    print(f"Pipeline: {fps:.0f} FPS ({ms:.3f} ms/frame)")