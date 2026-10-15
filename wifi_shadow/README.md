# Wi-Fi Shadow Sensing Layer (HaleHound-Fire Integration)

Passive RF shadow mapping for non-line-of-sight hazard detection.

## What it does

Listens to ambient Wi-Fi 6 (5 GHz) and Wi-Fi 7 (6 GHz) access points plus
Bluetooth Low Energy beacons already present in the environment. Human bodies
(~60% water) attenuate these signals, creating measurable shadows. When a
signal path that was previously clear suddenly drops 4+ dB, the layer flags a
potential body in the path — a pedestrian in a crosswalk the cameras can't see
through fog, or someone stepping out of a driveway behind a parked truck.

## Why it does NOT see through walls

- At 5.5 GHz, drywall costs ~5 dB per wall, concrete ~15 dB.
- A 20 cm torso adds ~6 dB.
- Free-space loss at 30 m is ~77 dB. Two walls + a body ≈ 93 dB total.
- With Wi-Fi 6's 30 dBm EIRP cap and a –90 dBm noise floor, that's still
  detectable with ~27 dB of margin — but only for *shadows on existing
  signals*, not for imaging through solid barriers.
- Wavelength is 5.5 cm, so resolution is centimeter-scale. Person-sized
  shadows, yes. Wall penetration imaging, no.
- No active RF illumination. Fully passive — the vehicle only receives.

## Files

- `src/wifi_shadow.py` — core sensor, physics helpers, pipeline hook
- `tests/test_wifi_shadow.py` — 13 unit tests

## Integration

The `WifiShadowSensor` class exposes `detect()` which returns a
`WifiShadowState` with detections, shadow density, and an optional advisory
string. The advisory feeds into the same decision layer as map-context and
traction advisories. High shadow density (>30% of surveyed paths) triggers a
speed-reduction advisory.

## Privacy

Aggregates RSSI only. No MAC-level tracking, no device identification, no
stored location history. See SAFETY_CASE.md.

## Status

Scaffold + physics model + unit tests. Real AP/BLE ingestion requires the
HaleHound-Fire tablet bridge (Kotlin, separate repo) feeding RSSI samples
into `update_access_points()` / `update_beacons()`.
