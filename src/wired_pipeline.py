# Author: Joseph Rocco Peransi
"""Wired pipeline that uses the shared feature buffer and Fast BEV.

Local entry point for testing on a laptop without nuScenes data.
Runs synthetic frames through the full stack and prints advisories.
"""

from __future__ import annotations

from shared_feature_buffer import SharedFeatureBuffer
from fast_bev import FastBevLookup
from integrated_pipeline import (
    PipelineFrame, WifiShadowState, ShadowDetection,
    integrated_speed_advisory,
)


def run_synthetic_test(n_frames: int = 5) -> None:
    print("=== OMNI-AWARE wired synthetic test ===")
    buf = SharedFeatureBuffer()
    bev = FastBevLookup(image_w=640, image_h=480)
    buf.register_head("ransac")
    buf.register_head("fusion")
    buf.register_head("decision")

    scenarios = [
        {"name": "clear dry", "grip": 0.9, "wet": 0.1, "curv": 0.1, "sight": 100,
         "shadow_d": 0.0, "rgb": [0.3, 0.5, 0.2]},
        {"name": "wet sharp", "grip": 0.4, "wet": 0.8, "curv": 0.5, "sight": 30,
         "shadow_d": 0.4, "rgb": [0.1, 0.2, 0.4]},
        {"name": "fog shadow", "grip": 0.8, "wet": 0.3, "curv": 0.2, "sight": 60,
         "shadow_d": 0.5, "rgb": [0.4, 0.4, 0.5]},
    ]

    for i, sc in enumerate(scenarios):
        frame = {"rgb_mean": sc["rgb"], "quadrant_activity": [0.1, 0.2, 0.15, 0.3]}
        handle = buf.process_once(frame, timestamp_ms=i * 100)
        # Demonstrate zero-copy style read
        mean = buf.read(handle, "rgb_mean")
        # BEV projection of image center
        bev_pt = bev.project(320, 240)
        shadow = WifiShadowState(
            detections=[ShadowDetection(0, 20, 0.7, "wifi", 0.5, i)] if sc["shadow_d"] > 0 else [],
            shadow_density=sc["shadow_d"],
        )
        pf = PipelineFrame(
            base_speed=60, grip=sc["grip"], wetness=sc["wet"],
            curvature=sc["curv"], sight_m=sc["sight"], shadow_state=shadow,
        )
        adv = pf.run()
        print(f"Frame {i} ({sc['name']}): advisory={adv:.1f} km/h  "
              f"rgb={mean}  bev_center={bev_pt}  heads={buf.alive_heads()}")
        if pf.advisories:
            for a in pf.advisories:
                print(f"  -> {a}")

    print("\nStopping-distance example (40 mph, 95% latency cut):")
    from shared_feature_buffer import stopping_distance_saved_m
    print(f"  saved ≈ {stopping_distance_saved_m(40.0):.2f} m")
    print("=== done ===")


if __name__ == "__main__":
    run_synthetic_test()
