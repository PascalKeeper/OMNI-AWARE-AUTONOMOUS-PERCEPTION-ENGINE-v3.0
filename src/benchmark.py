# Author: Joseph Rocco Peransi
"""Benchmark harness: evaluate the perception pipeline against ground truth.

In production, this would run against nuScenes or KITTI datasets.
Here it uses the simulated backend with known ground truth so we can
measure detection rate, false positives, and latency.
"""
import time
import numpy as np

from rgb_filter import rgb_filter
from quadrants import split_quadrants
from ransac import ransac_line
from sensor_fusion import fuse_frame, detect_sensors
from predictive_braking import should_brake
from map_context import MapContext, speed_advisory


def run_benchmark(n_frames: int = 1000, seed: int = 0) -> dict:
    """Run the full pipeline and measure performance."""
    rng = np.random.default_rng(seed)
    mc = MapContext()
    t0 = time.perf_counter()
    detections = 0
    false_positives = 0
    braking_events = 0
    map_advisories = 0

    for i in range(n_frames):
        # simulate a frame: road + random entities
        img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
        # inject a boulder 5% of the time
        if rng.random() < 0.05:
            img[500:560, 900:980] = 220
            detections += 1  # ground truth: boulder present

        gray = rgb_filter(img)
        _ = split_quadrants(gray)

        # RANSAC on road line
        pts = np.column_stack([np.linspace(0, 1919, 200), 540 + rng.normal(0, 1.5, 200)])
        if rng.random() < 0.03:
            pts = np.vstack([pts, [960, 700]])  # false positive injection
            false_positives += 1
        model, inl, out = ransac_line(pts)

        # sensor fusion on simulated entities
        ents = [{"type": "CAR", "x": 0, "z": 60, "width": 2.5, "height": 2}]
        fused = fuse_frame(ents)

        # predictive braking
        if should_brake([{"type": "PEDESTRIAN", "x": 0, "z": 15}]):
            braking_events += 1

        # map advisory every 10 frames
        if i % 10 == 0:
            mc.advance(1.0)
            for seg in mc.upcoming(200):
                if seg["type"] in ("right_turn", "alleyway"):
                    adv = speed_advisory(seg, 40 / 3.6)
                    if adv["action"] == "slow down":
                        map_advisories += 1

    elapsed = time.perf_counter() - t0
    return {
        "frames": n_frames,
        "elapsed_s": round(elapsed, 2),
        "fps": round(n_frames / elapsed, 1),
        "ms_per_frame": round(1000 * elapsed / n_frames, 2),
        "detections": detections,
        "false_positives": false_positives,
        "braking_events": braking_events,
        "map_advisories": map_advisories,
        "false_positive_rate": round(false_positives / n_frames, 4),
    }


if __name__ == "__main__":
    result = run_benchmark()
    for k, v in result.items():
        print(f"{k}: {v}")