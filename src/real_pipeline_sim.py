"""Real-pipeline simulation: models OMNI-AWARE's actual failure modes.

Unlike the perfect simulated detector (noisy GT copies), this models
what the real pipeline would do: distance-dependent detection,
increasing noise at range, false positives from shadows/reflections,
and color-dependent misses from the spectrum lock.
"""
import time
import numpy as np


class RealPipelineSim:
    """Simulates the real OMNI-AWARE pipeline's expected performance."""

    def __init__(self, seed=0):
        self.rng = np.random.default_rng(seed)

    def detect(self, gt_frame):
        """Run the real pipeline's detection logic on ground truth."""
        dets = []
        for obj in gt_frame:
            # detection probability drops with distance
            p_detect = max(0.3, 1.0 - obj["y"] / 150)
            if self.rng.random() < p_detect:
                noise = 0.05 + obj["y"] / 500
                dets.append({
                    "type": obj["type"],
                    "x": obj["x"] + self.rng.normal(0, noise),
                    "y": obj["y"] + self.rng.normal(0, noise),
                    "w": obj["w"], "h": obj["h"],
                    "confidence": max(0.2, 0.95 - obj["y"] / 200),
                })
        # false positives: shadows, reflections, overpasses
        if self.rng.random() < 0.15:
            dets.append({
                "type": self.rng.choice(["car", "barrier"]),
                "x": self.rng.uniform(-10, 10),
                "y": self.rng.uniform(10, 80),
                "w": 2.0, "h": 1.5,
                "confidence": self.rng.uniform(0.25, 0.55),
            })
        # color-dependent miss: pedestrian at night (spectrum lock kills contrast)
        for obj in gt_frame:
            if obj["type"] == "pedestrian" and self.rng.random() < 0.2:
                dets = [d for d in dets if not (
                    d["type"] == "pedestrian" and
                    abs(d["x"] - obj["x"]) < 1 and abs(d["y"] - obj["y"]) < 1)]
        return dets

    def match(self, gt, dets, threshold=2.5):
        """Greedy matching: center distance < threshold = TP."""
        matched_gt = set()
        tp = 0
        for d in dets:
            for i, g in enumerate(gt):
                if i in matched_gt:
                    continue
                dist = np.sqrt((d["x"] - g["x"]) ** 2 + (d["y"] - g["y"]) ** 2)
                if dist < threshold and d["type"] == g["type"]:
                    tp += 1
                    matched_gt.add(i)
                    break
        return tp, len(dets) - tp, len(gt) - len(matched_gt)

    def evaluate(self, n_scenes=20, frames=40):
        """Full evaluation with real-pipeline failure modes."""
        tp = fp = fn = 0
        lats = []
        for s in range(n_scenes):
            for f in range(frames):
                n_obj = self.rng.integers(0, 6)
                gt = [{
                    "type": self.rng.choice(["car", "pedestrian", "barrier"]),
                    "x": self.rng.uniform(-10, 10),
                    "y": self.rng.uniform(5, 100),
                    "w": self.rng.uniform(1.5, 4.5),
                    "h": self.rng.uniform(1.0, 2.2),
                } for _ in range(n_obj)]
                t0 = time.perf_counter()
                dets = self.detect(gt)
                lats.append((time.perf_counter() - t0) * 1000)
                t, p, n = self.match(gt, dets)
                tp += t; fp += p; fn += n
        prec = tp / max(tp + fp, 1)
        rec = tp / max(tp + fn, 1)
        f1 = 2 * prec * rec / max(prec + rec, 1e-9)
        return {
            "scenes": n_scenes,
            "frames": n_scenes * frames,
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1": round(f1, 3),
            "p50_ms": round(np.percentile(lats, 50), 2),
            "p99_ms": round(np.percentile(lats, 99), 2),
        }


if __name__ == "__main__":
    sim = RealPipelineSim()
    r = sim.evaluate()
    for k, v in r.items():
        print(f"{k}: {v}")
