# OMNI-AWARE v3.0 Safety Case

## 1. Scope

This document argues that OMNI-AWARE v3.0 is safe to use as a
**perception and advisory layer** — it detects hazards and recommends
actions, but does not actuate steering, braking, or acceleration.

## 2. Components and Claims

### 2.1 RGB Filter (21% R / 70% G / 7% B)
- **Claim**: Reduces data 3x, freeing cluster bandwidth.
- **Risk**: Destroys color information. Red brake lights, traffic signals,
  and lane markings are safety-critical and would be degraded.
- **Mitigation**: Filter is applied to a *copy* of the frame for the
  RANSAC/quadrant path only. The original RGB frame is preserved for
  color-dependent classification (signals, brake lights).
- **Status**: DOCUMENTED RISK. Not yet validated on real footage.

### 2.2 Sensor Fusion (v1.0.4 staged ranges)
- **Claim**: Radar at 150m, camera at 120m, lidar at 80m. Confidence climbs
  as sensors agree: sensors * 0.3 + 100/(z+1) * 0.1.
- **Risk**: Staged ranges assume ideal sensor placement and calibration.
- **Mitigation**: Confidence threshold (0.5) gates downstream decisions.
- **Status**: Logic verified by unit tests. Not validated on real sensors.

### 2.3 Predictive Braking (v1.0.4)
- **Claim**: Collision warning under 20m in ego lane (abs(x) < 20).
- **Risk**: 20m threshold may be too late at highway speeds.
  At 120 km/h, braking distance is ~79m.
- **Mitigation**: Map-aware layer (v3.1) extends the horizon to 200-500m,
  giving advisory lead time before the sensor threshold.
- **Status**: Threshold flagged for speed-adaptive revision.

### 2.4 CPU Spectrum Lock (v1.2.0-GOLD)
- **Claim**: CPU-bound processing bypasses GPU bus.
- **Risk**: 70/70/7 weighting crushes color. Same concern as 2.1, amplified.
- **Mitigation**: Same as 2.1 — applied to a copy, original preserved.
- **Status**: DOCUMENTED RISK. Recommend against using on production feeds
  until color-critical paths are proven independent.

### 2.5 Map-Aware Prediction (v3.1)
- **Claim**: Turn geometry, alleyways, driveways, crosswalks, school zones
  provide context beyond line-of-sight.
- **Risk**: Map data can be stale (construction, new driveways not mapped).
- **Mitigation**: Map advisories are advisory only; sensors remain the
  authority for immediate hazards.
- **Status**: Logic unit-tested. Backend is simulated; real OSRM/OSM
  integration pending.

## 3. Validation Plan

1. Run benchmark harness against nuScenes/KITTI public datasets.
2. Measure: detection rate, false positive rate, latency (p50/p99).
3. Compare fusion models: v0.9.4 (Kalman-style) vs v1.0.4 (staged ranges).
4. Field test on a closed course before any road deployment.
5. Independent review of this safety case.

## 4. Non-Claims

- This system does NOT control the vehicle.
- This system does NOT replace Tesla's production Autopilot stack.
- No actuation authority is granted to any component herein.
