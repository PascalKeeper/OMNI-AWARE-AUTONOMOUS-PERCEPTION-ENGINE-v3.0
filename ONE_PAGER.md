# OMNI-AWARE Perception Engine

**One-page summary for hiring conversations**

## What it is

A CPU-first autonomous perception prototype: RGB spectrum filter, quadrant-split sensor processing, RANSAC inlier/outlier detection, sensor fusion (radar/camera/lidar staged ranges), predictive braking, map-aware speed advisories, and a traction loop that cross-references wheel slip, visual surface cues, and acoustic tire noise.

## What it does well

- **Safety-first design**: every claim documented with a mitigation. The safety case covers the 20m braking threshold limitation, spectrum lock color destruction, and traction disagreement handling.
- **Honest benchmarking**: simulated detector F1 0.981 (proves the eval protocol); real-pipeline benchmark F1 0.722, precision 0.920, recall 0.593 — the recall gap is traced to distance decay and nighttime pedestrian misses, with documented fixes.
- **Measured performance**: Python baseline 82 FPS mean (60 median, 44 p99); C++ reference port with HW4-style mock showing 165+ FPS at 1080p and 300+ at 720p. The 422 FPS figure is a documented design target, not a measured claim.
- **Full lineage preserved**: v0.9.4, v1.0.4, v1.2.0-GOLD, map layer, traction loop, integrated pipeline, C++ port, and benchmark harness — nothing lost between iterations.

## What it is not

- Not production code. Not validated on real vehicle hardware. Not a claim to drive a car.
- The spectrum lock (70/70/7) destroys color-critical signals (brake lights, signals) and is flagged as unsafe for color-dependent paths.
- Real nuScenes evaluation is the next step — the harness and protocol are ready, the download is not yet run.

## Why it matters

This is a complete, documented prototype with a safety case, measured numbers, and an honest gap analysis. It demonstrates the ability to take an idea from concept through architecture, failure-mode analysis, and benchmark protocol — and to say what the system cannot do.

## Next steps

1. Run real pipeline against nuScenes mini (10 scenes) for genuinely measured numbers.
2. Isolate spectrum lock from color-critical detection paths.
3. Add temporal persistence filter (3+ frames) to cut false positives.
4. Validate braking threshold against real highway speeds.

---
*Built as a portfolio piece. Open to feedback, collaboration, and the next iteration.*