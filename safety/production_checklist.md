# Production Readiness Checklist — OMNI-AWARE v3.0

Before any component touches a real vehicle, the following must be validated.
This is a research/simulation project. Nothing here is production-ready.

## Perception Layer

- [ ] **Sensor fusion confidence model** validated against real multi-sensor data (not synthetic)
  - v1.0.4 staged ranges (radar 150m, camera 120m, lidar 80m) need real-world calibration
  - v0.9.4 Kalman model (base 0.5 + lidar 0.3 + camera 0.15) needs real sensor streams
- [ ] **Predictive braking threshold** (20m ego-lane) tested with real closing speeds and reaction times
- [ ] **RANSAC outlier rejection** benchmarked on real road imagery with known ground truth
- [ ] **RGB filter (21/70/7)** evaluated for information loss on safety-critical color signals

## Spectrum Lock — DO NOT DEPLOY

- [x] Ablation study completed: average chroma loss on colored signals measured
- [ ] If any deployment path is considered, a color-preserving alternative must be designed
  (e.g., HSV-based processing that retains hue while reducing data)

## AI Co-Pilot

- [ ] Grok API integration tested with real telemetry payloads and latency budgets
- [ ] Fallback behavior verified: local heuristics must be safe when API is unreachable
- [ ] Prompt injection and adversarial input testing
- [ ] Response time SLA defined (perception decisions cannot wait on LLM round-trips)

## Safety Architecture

- [ ] **No actuation path exists** — perception and display only (by design)
- [ ] Any future actuation requires Tesla's official API and independent safety validation
- [ ] Redundancy: critical decisions must not depend on a single software component
- [ ] Fail-safe defaults: system must degrade gracefully (e.g., to human driver) on any fault

## Testing

- [ ] Unit tests for all ported modules (fusion, braking, RANSAC, physics, decision)
- [ ] Integration test: full pipeline end-to-end with synthetic and real data
- [ ] Performance benchmark: target 60+ FPS sustained on target hardware
- [ ] Edge cases: sensor dropout, extreme weather, low light, occlusion

## Legal / Licensing

- [ ] GPL v3 implications reviewed for any commercial deployment
- [ ] Data privacy review for telemetry and camera data handling