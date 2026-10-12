# OMNI-AWARE Evaluation Results

## Simulated nuScenes Benchmark (v3.1)

| Metric | Value |
|--------|-------|
| Scenes | 20 |
| Frames | 800 |
| True Positives | 1978 |
| False Positives | 76 |
| False Negatives | 0 |
| **Precision** | **0.963** |
| **Recall** | **1.000** |
| **F1** | **0.981** |
| Latency p50 | 0.05 ms |
| Latency p99 | 0.16 ms |

## Important Caveats

These numbers come from a **simulated detector** that generates noisy
copies of ground truth. They demonstrate the evaluation protocol works,
not that the real pipeline performs at this level.

## Path to Real Numbers

1. Download nuScenes mini (or full) dataset from nuscenes.org
2. Install the official devkit: `pip install nuscenes-devkit`
3. Replace `NuScenesEval.run_detector()` with a wrapper that feeds each
   frame through the real OMNI-AWARE pipeline (rgb_filter -> quadrants ->
   ransac -> sensor_fusion -> predictive_braking)
4. Run `python src/nuscenes_eval.py` and replace this table with measured values
5. Compare against Tesla's published Autopilot metrics where available

## What Real nuScenes Adds

- 1000 scenes across Boston and Singapore
- 6 cameras per frame (front, front-left, front-right, back-left, back-right, back)
- 32-beam lidar point clouds
- Radar tracks
- GPS/IMU ground truth trajectories
- Official mAP and NDS metrics

## Next Steps

- [ ] Swap simulated detector for real pipeline
- [ ] Run on nuScenes mini (10 scenes) as a smoke test
- [ ] Run on full dataset for publication-grade numbers
- [ ] Add traction loop evaluation (wet/dry surface scenarios)
- [ ] Add map-aware advisory evaluation (did the system slow down before the turn?)
