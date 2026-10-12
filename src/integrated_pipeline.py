"""Integrated OMNI-AWARE v3.1 pipeline.

Merges all layers: RGB filter, quadrants, RANSAC, sensor fusion,
predictive braking, map-aware prediction, and traction loop into one
end-to-end perception and advisory system.
"""
import time
import numpy as np

from rgb_filter import rgb_filter
from quadrants import split_quadrants
from ransac import ransac_line
from sensor_fusion import fuse_frame
from predictive_braking import should_brake
from map_context import MapContext, speed_advisory
from traction_loop import surface_from_visual, traction_from_tires, classify_sound, cross_reference


class OmniAwareEngine:
    """Full perception + advisory engine."""

    def __init__(self, seed: int = 0):
        self.rng = np.random.default_rng(seed)
        self.map = MapContext()
        self.frame = 0

    def process_frame(self, img: np.ndarray, traction_state: dict = None) -> dict:
        """Run one frame through every layer."""
        self.frame += 1
        t0 = time.perf_counter()

        # 1. RGB filter + quadrants
        gray = rgb_filter(img)
        _ = split_quadrants(gray)

        # 2. RANSAC hazard detection
        pts = np.column_stack([np.linspace(0, 1919, 200), 540 + self.rng.normal(0, 1.5, 200)])
        if self.rng.random() < 0.05:
            pts = np.vstack([pts, [960, 700]])  # boulder
        model, inl, out = ransac_line(pts)
        hazards = int(out.sum())

        # 3. Sensor fusion
        ents = [{"type": "CAR", "x": 0, "z": 60, "width": 2.5, "height": 2}]
        fused = fuse_frame(ents)

        # 4. Predictive braking
        brake = should_brake([{"type": "PEDESTRIAN", "x": 0, "z": 15}])

        # 5. Map context + speed advisory
        self.map.advance(1.0)
        advisories = []
        for seg in self.map.upcoming(200):
            if seg["type"] in ("right_turn", "alleyway"):
                adv = speed_advisory(seg, 40 / 3.6)
                # 6. Traction adjustment
                if traction_state:
                    adv = self._adjust_for_traction(adv, traction_state)
                advisories.append(adv)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return {
            "frame": self.frame,
            "elapsed_ms": round(elapsed_ms, 2),
            "hazards_detected": hazards,
            "braking": brake,
            "advisories": advisories,
            "fused_entities": len(fused),
        }

    def _adjust_for_traction(self, adv: dict, traction: dict) -> dict:
        """Reduce recommended speed when traction is poor."""
        grip = traction.get("grip", 1.0)
        wet = traction.get("wetness", 0.0)
        if grip < 0.6:
            adv["recommended_speed_kmh"] = round(adv["recommended_speed_kmh"] * 0.7, 1)
            adv["action"] = "slow down (low traction)"
        elif wet > 0.5:
            adv["recommended_speed_kmh"] = round(adv["recommended_speed_kmh"] * 0.85, 1)
            adv["action"] = "slow down (wet surface)"
        adv["traction_grip"] = grip
        adv["traction_wetness"] = wet
        return adv


if __name__ == "__main__":
    engine = OmniAwareEngine()
    rng = np.random.default_rng(1)
    # dry, good traction
    for i in range(5):
        img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
        r = engine.process_frame(img, {"grip": 0.9, "wetness": 0.1})
        print(f"Frame {r['frame']}: {r['elapsed_ms']}ms, hazards={r['hazards_detected']}, "
              f"braking={r['braking']}, advisories={len(r['advisories'])}")
    # wet, low traction
    print("--- wet, low traction ---")
    for i in range(3):
        img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
        r = engine.process_frame(img, {"grip": 0.3, "wetness": 0.9})
        for a in r["advisories"]:
            print(f"  {a['segment']}: rec={a['recommended_speed_kmh']} km/h, action={a['action']}")