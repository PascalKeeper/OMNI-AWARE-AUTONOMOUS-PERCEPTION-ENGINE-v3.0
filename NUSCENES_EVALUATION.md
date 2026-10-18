# nuScenes mini evaluation

Real run of the OMNI-AWARE v3 camera path on nuScenes v1.0-mini. The harness is `src/nuscenes_eval.py`. Frames come from `nuscenes_adapter.py` with dataroot `C:\data\sets\nuscenes`. Detections come from `nuscenes_detector.py`.

`src/wired_pipeline.py` is a synthetic speed-advisory demo, not a box detector. The bridge runs the RGB filter once, stores the filtered image in `SharedFeatureBuffer`, and has the RANSAC and fusion heads read that handle. Lidar sweeps are not a detection source. `sensor_fusion` only range-gates a distance.

Matching is the existing greedy rule: same type and center distance under 2 m in the ego frame (`x` forward, `y` left). `vehicle.car` and `vehicle.truck` map to `vehicle`. Pedestrians stay `pedestrian`. Barriers, cones, and debris are `obstacle`. Other categories are skipped (1,516 annotations: bus, trailer, construction, bicycle, motorcycle, pushable objects, bicycle racks).

## Result

| Metric | This run | Simulated detector | Real-pipeline simulation |
| --- | ---: | ---: | ---: |
| Precision | 0.006 | 0.963 | 0.920 |
| Recall | 0.003 | 1.000 | 0.593 |
| F1 | 0.004 | 0.981 | 0.722 |
| Median latency | 44.20 ms | 8.39 ms | 12.0 ms |
| 99th percentile latency | 60.28 ms | 15.24 ms | not reported |
| False positives | 8662 | not reported | not reported |
| Missed detections | 16974 | not reported | not reported |

10 scenes, 404 samples, 0 skipped samples. True positives: 48. Raw rows are in `nuscenes_results.csv`. The aggregate is in `nuscenes_summary.json`.

By type: `vehicle` 8,268 ground truth, recall 0.000. `pedestrian` 5,040, recall 0.000. `obstacle` 3,714, 48 hits, recall 0.013.

## Baseline comparison

### Simulated detector (F1 0.981)

That baseline copies each ground-truth box, jitters it by about 0.3 m, and drops nothing. Its recall is 1.0 by construction. This run's F1 is 0.004. The camera path never emits `vehicle` or `pedestrian`, so those 13,308 objects cannot match. The 48 hits are all `obstacle` and all inside 20 m.

### Real-pipeline simulation (F1 0.722)

`tests/test_real_pipeline_sim.py` feeds `real_pipeline_sim.simulate_pipeline_on_gt`, which starts from the labels and then applies spectrum lock, a 15% false-positive draw, and a distance curve. Measured F1 there is 0.722 (precision 0.920, recall 0.593). This nuScenes run does not execute that simulator. It executes the modules, and the F1 falls to 0.004.

## Observed failure modes

### Spectrum lock color destruction — not observed

The bridge calls `rgb_filter` (weights 0.21, 0.70, 0.07). It does not call `spectrum_lock` (0.70, 0.70, 0.07). Pedestrian recall and vehicle recall are both 0.000. Night scenes `scene-1077`, `scene-1094`, and `scene-1100` are in the run, and vehicles fail the same way pedestrians do. There is no color-class effect to attribute to spectrum lock.

### Far-range decay past 150 m — not the mode in EVALUATION.md

`EVALUATION.md` models detection probability as `max(0.3, 1 - distance/150)`, so objects past 150 m would still be detected about 30% of the time and nearer objects much more often. The mapped labels contain 3 objects past 150 m, all missed. Recall is also 0.000 from 20 m outward (8,779 at 20–50 m, 2,627 at 50–80 m, 375 at 80–120 m, 32 at 120–150 m) and 0.009 inside 20 m. The miss is flat.

Frame: `scene-0553` ("Wait at intersection, bicycle, large truck, peds crossing crosswalk, ped with stroller"), sample `8687ba92abd3406aa797115b874ebeba`. Two objects beyond 150 m, max range 158.47 m, 23 detections, 0 true positives. Every detection sits between 12.12 m and 13.66 m.

### Shadow false positives — not the mode in EVALUATION.md

The simulation plants one extra `car` or `barrier` on 15% of frames. This run produced 8,662 false positives, about 21 per frame, every one typed `obstacle`. No frame had zero ground truth and a detection. The RANSAC scanline outlier fraction is 0.694. The threshold in `ransac.py` is 2.0 intensity units, sized for synthetic noise around 1.5, not an 8-bit road row.

Frame: `scene-0757` ("Arrive at busy intersection, bus, wait at intersection, bicycle, peds"), sample `a9def8f915cf4bfe9c74b864384ec6c7`. 12 ground-truth objects, 33 detections, 0 true positives. Detection ranges 12.12–13.72 m.

## What the run did show

1. **No class head.** Vehicles and pedestrians are never detected. The only matches are 48 obstacles of 3,714. Highest-miss frame: `scene-0061` ("Parked truck, construction, intersection, turn left, following a van"), sample `b26e791522294bec90f86fd72226e35c`, 149 ground-truth objects, 43 pedestrians, 147 misses. Detections stay inside 12.12–13.59 m.

2. **One scanline, one distance.** Road-quadrant RANSAC fits luminance on a single row and the bridge places those outliers on a fixed ground plane. Detections cluster at about 12–14 m. Recall is 0 past 20 m.

3. **Threshold-scale false positives.** Outlier fraction 0.694. Precision is 0.006. A true-positive frame is still mostly misses: `scene-0061`, sample `ca9a282c9e77460f8360f564131a8af5`, 2 hits, 27 false positives, 63 misses, 30 pedestrians in the labels, detections at 12.12–13.66 m.

## Fixes, by impact

1. **Emit classed 3D boxes, or stop treating scanline outliers as objects.** Nothing else changes vehicle or pedestrian recall. This is the whole F1 gap against both baselines.
2. **Scale the RANSAC threshold to the scanline.** A residual of 2.0 does not mean "hazard" on 8-bit pixels. That cuts the 8,662 false positives. It does not create the missing classes.
3. **Use more than one image row, or read the lidar sweep.** The pipeline ignores the point cloud. Multiple rows or lidar points are what would give a range other than ~12 m.
4. **Keep spectrum lock off this path.** It was not involved. The 70/70/7 weights would add the color failure `EVALUATION.md` already describes.
5. **A 3-frame temporal filter** only matters after detections are sparse and classed. It does not fix 21 false obstacles per frame from the same scanline.
