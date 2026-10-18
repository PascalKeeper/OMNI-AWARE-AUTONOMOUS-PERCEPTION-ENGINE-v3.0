"""nuScenes-style evaluation harness.

Simulates the official nuScenes evaluation protocol: per-frame detection
against ground truth, greedy matching, precision/recall/F1, and latency
percentiles. The detector here is simulated; swap it for the real
OMNI-AWARE pipeline and these become measured numbers.

The live path points this same matcher at an adapter module and a
detector module:

    python src/nuscenes_eval.py --adapter nuscenes_adapter.py --detector nuscenes_detector.py
"""
import csv
import importlib.util
import json
import os
import sys
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
        """Greedy matching: center distance < threshold and same type = TP."""
        tp, fp, fn, _pairs, _matched = self.match_detailed(gt, dets, threshold)
        return tp, fp, fn

    def match_detailed(self, gt, dets, threshold=2.0):
        """Same greedy match, plus the matched ground-truth indexes."""
        matched_gt = set()
        pairs = []
        for di, d in enumerate(dets):
            for i, g in enumerate(gt):
                if i in matched_gt:
                    continue
                dist = np.sqrt((d["x"] - g["x"]) ** 2 + (d["y"] - g["y"]) ** 2)
                if dist < threshold and d["type"] == g["type"]:
                    matched_gt.add(i)
                    pairs.append((i, di, float(dist)))
                    break
        tp = len(pairs)
        fp = len(dets) - tp
        fn = len(gt) - len(matched_gt)
        return tp, fp, fn, pairs, matched_gt

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


def _load_module(path, name):
    """Load a project-root module by file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _range_bin(distance):
    edges = (20, 50, 80, 120, 150)
    labels = ("0-20", "20-50", "50-80", "80-120", "120-150", "150+")
    for edge, label in zip(edges, labels):
        if distance < edge:
            return label
    return labels[-1]


def _empty_type_counts():
    return {key: {"gt": 0, "tp": 0} for key in ("vehicle", "pedestrian", "obstacle")}


def evaluate_live(adapter, detect_fn, csv_path, summary_path):
    """Score detect_fn on every frame the adapter yields.

    Matching is NuScenesEval.match. Per-frame rows go to csv_path and
    the aggregate, including the raw counts the report needs, goes to
    summary_path.
    """
    ev = NuScenesEval(seed=0)
    total_tp = total_fp = total_fn = 0
    latencies = []
    scenes = {}
    type_counts = _empty_type_counts()
    range_counts = {
        label: {"gt": 0, "tp": 0}
        for label in ("0-20", "20-50", "50-80", "80-120", "120-150", "150+")
    }
    examples = []
    rows = []
    frames = 0
    outlier_points_total = [0]
    scan_points_total = [0]

    for frame in adapter.iter_frames():
        frames += 1
        gt = frame["ground_truth"]
        t0 = time.perf_counter()
        dets = detect_fn(frame) or []
        latency_ms = (time.perf_counter() - t0) * 1000
        latencies.append(latency_ms)
        tp, fp, fn, _pairs, matched = ev.match_detailed(gt, dets)
        total_tp += tp
        total_fp += fp
        total_fn += fn
        stats = getattr(detect_fn, "frame_stats", None) or {}
        if stats.get("scan_points"):
            outlier_points_total[0] += int(stats["outlier_points"])
            scan_points_total[0] += int(stats["scan_points"])
        scene_name = frame.get("scene_name", "")
        scenes.setdefault(scene_name, {"token": frame.get("scene_token", ""), "frames": 0})
        scenes[scene_name]["frames"] += 1

        gt_ranges = []
        for i, obj in enumerate(gt):
            kind = obj["type"]
            if kind not in type_counts:
                type_counts[kind] = {"gt": 0, "tp": 0}
            type_counts[kind]["gt"] += 1
            if i in matched:
                type_counts[kind]["tp"] += 1
            distance = float(np.hypot(obj["x"], obj["y"]))
            gt_ranges.append(round(distance, 2))
            bucket = _range_bin(distance)
            range_counts[bucket]["gt"] += 1
            if i in matched:
                range_counts[bucket]["tp"] += 1

        det_ranges = [round(float(d.get("distance", np.hypot(d["x"], d["y"]))), 2) for d in dets]
        row = {
            "scene_name": scene_name,
            "scene_token": frame.get("scene_token", ""),
            "sample_token": frame.get("sample_token", ""),
            "timestamp": frame.get("timestamp", ""),
            "image_path": frame.get("image_path", ""),
            "n_gt": len(gt),
            "n_det": len(dets),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "latency_ms": round(latency_ms, 3),
            "gt_types": ",".join(obj["type"] for obj in gt),
            "det_types": ",".join(d.get("type", "") for d in dets),
            "gt_range_m": " ".join(str(v) for v in gt_ranges),
            "det_range_m": " ".join(str(v) for v in det_ranges),
        }
        rows.append(row)
        examples.append(
            {
                "scene_name": scene_name,
                "scene_description": frame.get("scene_description", ""),
                "sample_token": frame.get("sample_token", ""),
                "image_path": frame.get("image_path", ""),
                "timestamp": frame.get("timestamp", ""),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "n_gt": len(gt),
                "n_det": len(dets),
                "gt_types": row["gt_types"],
                "max_gt_range_m": max(gt_ranges) if gt_ranges else 0.0,
                "n_gt_beyond_150": sum(1 for v in gt_ranges if v >= 150.0),
                "n_pedestrian": sum(1 for obj in gt if obj["type"] == "pedestrian"),
                "det_range_min_m": min(det_ranges) if det_ranges else None,
                "det_range_max_m": max(det_ranges) if det_ranges else None,
            }
        )
        if frames % 25 == 0:
            print(f"frames {frames}  tp={total_tp} fp={total_fp} fn={total_fn}", flush=True)

    precision = total_tp / max(total_tp + total_fp, 1)
    recall = total_tp / max(total_tp + total_fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    lat = np.asarray(latencies, dtype=float) if latencies else np.array([0.0])

    def _recall(bucket):
        gt_n = bucket["gt"]
        return round(bucket["tp"] / gt_n, 3) if gt_n else None

    beyond = range_counts["150+"]
    summary = {
        "scenes": len(scenes),
        "frames": frames,
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "missed_detections": total_fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "latency_p50_ms": round(float(np.percentile(lat, 50)), 2),
        "latency_p99_ms": round(float(np.percentile(lat, 99)), 2),
        "by_type": {
            name: {**counts, "recall": _recall(counts)}
            for name, counts in type_counts.items()
        },
        "by_range_m": {
            name: {**counts, "recall": _recall(counts)}
            for name, counts in range_counts.items()
        },
        "gt_beyond_150m": beyond["gt"],
        "tp_beyond_150m": beyond["tp"],
        "scene_frames": scenes,
        "skipped_samples": int(getattr(adapter, "STATS", {}).get("skipped_samples", 0)),
        "skipped_annotations": int(getattr(adapter, "STATS", {}).get("skipped_annotations", 0)),
        "skipped_categories": dict(getattr(adapter, "STATS", {}).get("skipped_categories", {})),
        "mapped_categories": dict(getattr(adapter, "STATS", {}).get("mapped", {})),
        "ransac_outlier_fraction": (
            round(outlier_points_total[0] / scan_points_total[0], 3)
            if scan_points_total[0] else None
        ),
        "baselines": {
            "simulated_detector_f1": 0.981,
            "simulated_detector_precision": 0.963,
            "simulated_detector_recall": 1.000,
            "real_pipeline_sim_f1": 0.722,
            "real_pipeline_sim_precision": 0.920,
            "real_pipeline_sim_recall": 0.593,
        },
    }
    # A few concrete frames for the write-up. Highest FP, highest FN,
    # any far-range ground truth, and any true positive.
    if examples:
        summary["examples"] = {
            "highest_fp": max(examples, key=lambda e: (e["fp"], e["n_det"])),
            "highest_fn": max(examples, key=lambda e: (e["fn"], e["n_gt"])),
            "beyond_150m": next((e for e in examples if e["n_gt_beyond_150"] > 0), None),
            "pedestrian": next((e for e in examples if e["n_pedestrian"] > 0), None),
            "true_positive": next((e for e in examples if e["tp"] > 0), None),
            "zero_gt_with_detections": next(
                (e for e in examples if e["n_gt"] == 0 and e["n_det"] > 0), None
            ),
        }

    os.makedirs(os.path.dirname(os.path.abspath(csv_path)) or ".", exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["frames"])
        writer.writeheader()
        writer.writerows(rows)
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("examples", "scene_frames")}, indent=2))
    print(f"wrote {csv_path}")
    print(f"wrote {summary_path}")
    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OMNI-AWARE nuScenes evaluation")
    parser.add_argument("--adapter", default=None, help="Path to nuscenes_adapter.py")
    parser.add_argument("--detector", default=None, help="Path to nuscenes_detector.py")
    parser.add_argument("--csv", default="nuscenes_results.csv")
    parser.add_argument("--summary", default="nuscenes_summary.json")
    args = parser.parse_args()
    if args.adapter and args.detector:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if root not in sys.path:
            sys.path.insert(0, root)
        adapter = _load_module(os.path.abspath(args.adapter), "nuscenes_adapter")
        detector = _load_module(os.path.abspath(args.detector), "nuscenes_detector")
        evaluate_live(adapter, detector.detect, args.csv, args.summary)
    else:
        ev = NuScenesEval(n_scenes=20, frames_per_scene=40)
        result = ev.evaluate()
        for k, v in result.items():
            print(f"{k}: {v}")