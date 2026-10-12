"""nuScenes-style evaluation harness.

Simulates the official nuScenes evaluation protocol: per-frame detection
against ground truth, greedy matching, precision/recall/F1, and latency
percentiles. The detector here is simulated; swap it for the real
OMNI-AWARE pipeline and these become measured numbers.
"""
import time
import numpy as np


class NuScenesEval:
    """Simulated nuScenes evaluation."""

    def __init__(self, n_scenes=10, frames_per_scene=40, seed=0):
        self.rng = np.random.default_rng(seed)
        self.n_scenes = n_scenes
        self.frames_per_scene = frames_per_scene

    def generate_scene(self):
        """One scene: sequence of frames with ground-truth objects."""
        frames = []
        for f in range(self.frames_per_scene):
            n_obj = self.rng.integers(0, 6)
            gt = []
            for _ in range(n_obj):
                gt.append({
                    "type": self.rng.choice(["car", "pedestrian", "barrier"]),
                    "x": self.rng.uniform(-10, 10),
                    "y": self.rng.uniform(5, 100),
                    "w": self.rng.uniform(1.5, 4.5),
                    "h": self.rng.uniform(1.0, 2.2),
                })
            frames.append(gt)
        return frames

    def run_detector(self, gt_frame, noise=0.1):
        """Simulate detector: noisy GT copies + random false positives."""
        dets = []
        for obj in gt_frame:
            dets.append({
                "type": obj["type"],
                "x": obj["x"] + self.rng.normal(0, noise),
                "y": obj["y"] + self.rng.normal(0, noise),
                "w": obj["w"], "h": obj["h"],
                "confidence": self.rng.uniform(0.5, 0.99),
            })
        if self.rng.random() < 0.10:
            dets.append({
                "type": "car",
                "x": self.rng.uniform(-10, 10),
                "y": self.rng.uniform(5, 100),
                "w": 2.0, "h": 1.5,
                "confidence": self.rng.uniform(0.3, 0.6),
            })
        return dets

    def match(self, gt, dets, threshold=2.0):
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
        fp = len(dets) - tp
        fn = len(gt) - len(matched_gt)
        return tp, fp, fn

    def evaluate(self):
        """Full evaluation across all scenes."""
        total_tp = total_fp = total_fn = 0
        latencies = []
        for s in range(self.n_scenes):
            scene = self.generate_scene()
            for gt in scene:
                t0 = time.perf_counter()
                dets = self.run_detector(gt)
                latencies.append((time.perf_counter() - t0) * 1000)
                tp, fp, fn = self.match(gt, dets)
                total_tp += tp
                total_fp += fp
                total_fn += fn
        precision = total_tp / max(total_tp + total_fp, 1)
        recall = total_tp / max(total_tp + total_fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-9)
        return {
            "scenes": self.n_scenes,
            "frames": self.n_scenes * self.frames_per_scene,
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "latency_p50_ms": round(np.percentile(latencies, 50), 2),
            "latency_p99_ms": round(np.percentile(latencies, 99), 2),
        }


if __name__ == "__main__":
    ev = NuScenesEval(n_scenes=20, frames_per_scene=40)
    result = ev.evaluate()
    for k, v in result.items():
        print(f"{k}: {v}")