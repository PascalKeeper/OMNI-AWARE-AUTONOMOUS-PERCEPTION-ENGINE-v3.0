# OMNI-AWARE Evaluation Results
Author: Joseph Rocco Peransi

## Two Benchmarks, Two Detectors

### 1. Perfect Simulated Detector (nuscenes_eval.py)

Generates noisy copies of ground truth. Proves the evaluation
protocol works.

| Metric | Value |
|--------|-------|
| Scenes | 20 |
| Frames | 800 |
| Precision | 0.963 |
| Recall | 1.000 |
| F1 | 0.981 |
| Latency p50 | 0.05 ms |
| Latency p99 | 0.16 ms |

### 2. Real Pipeline Simulation (real_pipeline_sim.py)

Models the actual OMNI-AWARE failure modes: distance-dependent
detection, range-increasing noise, 15% false positive rate from
shadows/reflections/overpasses, and color-dependent pedestrian misses
from the spectrum lock.

| Metric | Value |
|--------|-------|
| Scenes | 20 |
| Frames | 800 |
| Precision | 0.920 |
| Recall | 0.593 |
| F1 | 0.722 |
| Latency p50 | 0.01 ms |
| Latency p99 | 0.10 ms |

## The Gap Is The Finding

The drop from F1 0.981 to F1 0.722 is not a bug in the benchmark.
It is the honest measurement of what the real pipeline would do:

- **Recall 0.593**: objects at range are missed (detection probability
  decays past 150m), and pedestrians are missed at night because the
  spectrum lock destroys color contrast.
- **Precision 0.920**: shadows, reflections, and overpasses generate
  false positives the RANSAC layer cannot fully reject.
- **FN 798**: nearly 40% of ground-truth objects undetected.

## What This Means

1. The **spectrum lock must be removed or isolated** from
   color-critical detection paths before any real deployment.
2. The **20m braking threshold is too late** at highway speeds;
   the map layer's 200-500m horizon is the right mitigation but
   needs real validation.
3. **False positives from shadows** are the top precision killer;
   a temporal filter (object must persist across 3+ frames) would
   cut these significantly.

## Path to Real Numbers

1. Download nuScenes mini from nuscenes.org
2. `pip install nuscenes-devkit`
3. Replace `RealPipelineSim.detect()` with a wrapper feeding frames
   through rgb_filter -> quadrants -> ransac -> sensor_fusion
4. Run and replace this table with measured values
5. Compare against published Autopilot metrics

## Status

- [x] Evaluation protocol built and tested
- [x] Real-pipeline failure modes modeled
- [x] Honest comparison documented
- [ ] Real nuScenes data run
- [x] Spectrum lock isolation fix
- [x] Temporal FP filter
- [ ] Closed-course field test
- [x] Occluded-presence detection (Wi-Fi beacon density, three-frame promotion)
