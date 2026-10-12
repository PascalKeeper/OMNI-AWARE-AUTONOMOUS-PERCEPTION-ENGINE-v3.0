# OMNI-AWARE v3.1 Safety Case

## 1. Scope

Perception and advisory layer only. No actuation authority.

## 2. Components and Claims

### 2.1 RGB Filter (21% R / 70% G / 7% B)
- **Claim**: Reduces data 3x.
- **Risk**: Destroys color. Brake lights, signals degraded.
- **Mitigation**: Applied to a copy; original RGB preserved for color paths.
- **Status**: DOCUMENTED RISK.

### 2.2 Sensor Fusion (v1.0.4 staged ranges)
- Radar 150m, camera 120m, lidar 80m. Confidence: sensors*0.3 + 100/(z+1)*0.1.
- **Status**: Unit-tested. Not validated on real sensors.

### 2.3 Predictive Braking (v1.0.4)
- Warning under 20m in ego lane. Too late at highway speed (79m brake distance at 120 km/h).
- **Mitigation**: Map layer extends horizon to 200-500m.
- **Status**: Threshold flagged for speed-adaptive revision.

### 2.4 CPU Spectrum Lock (v1.2.0-GOLD)
- 70/70/7 pixel weighting. Same color-destruction risk as 2.1.
- **Status**: DOCUMENTED RISK. Not for production feeds.

### 2.5 Map-Aware Prediction (v3.1)
- Turn geometry, alleyways, driveways, crosswalks, school zones.
- **Risk**: Stale map data.
- **Mitigation**: Advisory only; sensors remain authority.
- **Status**: Unit-tested. Simulated backend; OSRM/OSM pending.

### 2.6 Traction Loop (v3.1)
- **Claim**: Cross-references wheel slip, visual surface (glimmer/gravelly),
  and acoustic signature (gravel hiss, water rumble, dry hum).
- **Risk**: Microphone noise, camera glare false positives.
- **Mitigation**: Three-signal agreement required for high-confidence actions.
  Disagreement triggers 'check' advisories, not emergency actions.
- **Status**: Unit-tested (12 tests). Not validated on real vehicles.

### 2.7 Integrated Pipeline (v3.1)
- All layers run end-to-end per frame. Traction state adjusts map advisories:
  grip < 0.6 -> 30% speed reduction; wet > 0.5 -> 15% reduction.
- **Status**: Unit-tested.

### 2.8 UV Fluorescence Sensing (Future Hardware)
- **Proposal**: UV illuminator + sensor without IR cut filter for
  night-vision pedestrian detection via clothing fluorescence.
- **Risk**: Eye safety, false positives from non-clothing fluorescers,
  range limits, cost.
- **Status**: PROPOSAL ONLY. See FUTURE_HARDWARE.md.

## 3. Validation Plan

1. Benchmark against nuScenes/KITTI.
2. Measure detection rate, false positives, p50/p99 latency.
3. Compare fusion models side by side.
4. Closed-course field test with real traction data.
5. Independent safety review.

## 4. Non-Claims

- Does NOT control the vehicle.
- Does NOT replace Tesla Autopilot.
- No actuation authority granted.
