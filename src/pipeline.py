"""Full OMNI-AWARE v3.0 pipeline: filter -> quadrants -> RANSAC -> temporal -> Grok.

End-to-end perception loop. Each frame runs locally at ~218 FPS.
Only hazards that persist for 3 frames are escalated to Grok.

OMNI_FILTER_BACKEND selects the luminance filter. "python" is the
default and the current behavior. "numba" uses rgb_filter_numba when
that package imports, and falls back to the Python filter otherwise.
"""
from __future__ import annotations

import os
import time
import numpy as np

from rgb_filter import rgb_filter as python_rgb_filter, preserve_color
from quadrants import split_quadrants, assign_sensors
from ransac import ransac_line, detect_color_hazards
from physics import simulate_falling_object, predict_evasion
from decision import decide, DEFAULT_SCENARIO
from grok_client import analyze_hazard
from temporal_filter import TemporalFilter, project_to_meters
from fast_bev import FastBevLookup
from wifi_scan import WifiScanner


def active_rgb_filter():
    """Return the Python filter unless OMNI_FILTER_BACKEND=numba imports."""
    backend = os.environ.get("OMNI_FILTER_BACKEND", "python").strip().lower()
    if backend != "numba":
        return python_rgb_filter
    try:
        from rgb_filter_numba import rgb_filter as compiled
    except Exception:
        return python_rgb_filter
    return compiled


class PerceptionEngine:
    """CPU-first perception pipeline with optional cloud escalation."""

    def __init__(self, api_key: str = None, escalate_threshold: int = 5):
        self.api_key = api_key
        self.escalate_threshold = escalate_threshold  # min outliers to trigger Grok
        self.frame_count = 0
        self.hazard_log = []
        self.temporal = TemporalFilter()
        self.wifi = WifiScanner(live=False)
        self._bev = None
        self._bev_shape = None

    def _bev_for(self, height: int, width: int) -> FastBevLookup:
        if self._bev is None or self._bev_shape != (height, width):
            self._bev = FastBevLookup(image_w=width, image_h=height)
            self._bev_shape = (height, width)
        return self._bev

    def process_frame(self, img: np.ndarray, beacons: list | None = None, radar: bool = False) -> dict:
        """Run one frame through the full pipeline.

        `beacons` injects a Wi-Fi scan. When it is omitted, the scanner
        polls on its own interval (empty unless live=True). Occluded
        cells join the same temporal update as camera outliers.
        """
        self.frame_count += 1
        t0 = time.perf_counter()

        # 1. Color stays on the original frame. The filter writes a new gray buffer.
        color = preserve_color(img)
        gray = active_rgb_filter()(img)
        color_signals = detect_color_hazards(color)

        # 2. Quadrant split + sensor assignment
        qs = split_quadrants(gray)
        sensors = assign_sensors(qs)

        # 3. RANSAC per road quadrant
        hazards = []
        image_outliers = []
        full_h, full_w = gray.shape
        t_ransac = time.perf_counter()
        for name in ("road_left", "road_right"):
            road = sensors[name]
            H, W = road.shape
            xs = np.linspace(0, W - 1, 100)
            scan_row = H // 2
            ys = road[scan_row, xs.astype(int)].astype(float)
            pts = np.column_stack([xs, ys])
            model, inl, out = ransac_line(pts)
            outlier_pts = pts[out]
            u_off = 0.0 if name == "road_left" else float(full_w // 2)
            v = float(full_h // 2 + scan_row)
            for x_pix, _intensity in outlier_pts:
                image_outliers.append((float(x_pix) + u_off, v))
            if len(outlier_pts) >= self.escalate_threshold:
                hazards.append(
                    {
                        "quadrant": name,
                        "n_outliers": len(outlier_pts),
                        "outlier_points": outlier_pts.tolist(),
                    }
                )
        ransac_ms = (time.perf_counter() - t_ransac) * 1000

        # 3b. Wi-Fi density. A spike with no camera match and no radar
        # return is only a tentative occluded track.
        t_wifi = time.perf_counter()
        scanned = self.wifi.read_beacons() if beacons is None else list(beacons)
        flags = self.wifi.observe(scanned, visual=False, radar=radar)
        wifi_pts = self.wifi.track_points(flags)
        wifi_ms = (time.perf_counter() - t_wifi) * 1000

        # 4. One temporal update for camera points and occluded cells.
        # A second update would count a miss against the other set.
        t_fusion = time.perf_counter()
        camera_pts = project_to_meters(image_outliers, self._bev_for(full_h, full_w))
        points = list(camera_pts) + list(wifi_pts)
        labels = (["obstacle"] * len(camera_pts)) + (["occluded"] * len(wifi_pts))
        confirmed = self.temporal.update(
            points,
            frame=self.frame_count,
            labels=labels if labels else None,
        )
        fusion_ms = (time.perf_counter() - t_fusion) * 1000

        # 5. Escalate confirmed tracks only.
        grok_results = []
        for track in confirmed:
            result = analyze_hazard(gray, [list(track.centroid)], api_key=self.api_key)
            result["object_id"] = track.object_id
            result["persistent"] = True
            result["centroid"] = list(track.centroid)
            grok_results.append(result)
            self.hazard_log.append(result)

        # 5. Physics + decision if a falling-object hazard is present
        physics_result = None
        if any(r["hazard_type"] == "log" for r in grok_results):
            t, x_obj, x_truck, gap = simulate_falling_object()
            evasion = predict_evasion(gap)
            physics_result = {
                "time_to_impact_s": round(t, 2),
                "gap_m": round(gap, 1),
                "evasion": evasion,
            }

        # 6. Path decision for static hazards (cliff/waterfall)
        decision = None
        if any(r["hazard_type"] in ("cliff", "waterfall") for r in grok_results):
            choice, score, scores = decide(DEFAULT_SCENARIO)
            decision = {"choice": choice, "score": round(score, 2), "scores": scores}

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return {
            "frame": self.frame_count,
            "elapsed_ms": round(elapsed_ms, 2),
            "ransac_ms": round(ransac_ms, 3),
            "fusion_ms": round(fusion_ms, 3),
            "wifi_ms": round(wifi_ms, 3),
            "hazards_local": len(hazards),
            "confirmed_hazards": [
                {
                    "object_id": track.object_id,
                    "hit_count": track.hit_count,
                    "centroid": track.centroid,
                    "hazard_type": track.hazard_type,
                }
                for track in confirmed
            ],
            "color_signals": color_signals,
            "grok_results": grok_results,
            "physics": physics_result,
            "decision": decision,
        }


if __name__ == "__main__":
    engine = PerceptionEngine()  # no API key -> local fallback only
    rng = np.random.default_rng(1)
    for i in range(10):
        img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
        if i == 5:
            img[500:560, 900:980] = 220  # inject a boulder
        result = engine.process_frame(img)
        print(f"Frame {result['frame']}: {result['elapsed_ms']} ms, "
              f"ransac_ms={result['ransac_ms']}, fusion_ms={result['fusion_ms']}, "
              f"wifi_ms={result['wifi_ms']}, "
              f"local hazards={result['hazards_local']}, "
              f"grok={[r['hazard_type'] for r in result['grok_results']]}")