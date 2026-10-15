# Near-Field Ultrasonic Sonar Layer (Bat-Inspired Echolocation)

## What it does

Eight-transducer ultrasonic ring array (40 kHz) providing centimeter-scale
near-field perception from 0.3 to 10 meters. Complements the 77 GHz radar
(which handles 10-200+ m) and cameras (which fail in fog/darkness). This is
the layer that sees the curb, the shopping cart, the child stepping off the
sidewalk at two meters — where radar resolution is too coarse and cameras
are blind.

## Physics

- Speed of sound: 343 m/s at 20 C
- 40 kHz wavelength: 8.6 mm — sub-centimeter resolution
- Distance = (round-trip time x 343) / 2
- Doppler shift gives closing/opening speed
- Attenuation ~1.5-2 dB/m limits practical range to ~10 m
- 50 Hz ping rate, 2 ms chirp per transducer

## Transducer layout

4 front-facing (-45 to +45 deg), 2 side (-30/+30 at -0.5 m), 2 wide
(-60/+60). Bearings fuse across transducers for object localization.

## Classification heuristics

- Low amplitude + close (<2 m): curb or low debris
- High amplitude + wide (>1.5 m): vehicle
- Medium amplitude + Doppler motion: pedestrian
- Otherwise: unknown/debris

## Speed advisory integration

- Under 1 m: 90% speed cut (emergency floor at 5 km/h)
- 1-3 m: 50% cut
- 3-5 m: 25% cut
- Beyond 5 m: no cut

Stacks with map, traction, and RF shadow reductions. Worst case hits the
5 km/h floor.

## Hardware

Commercial parking-sensor arrays (Valeo, Bosch) provide the transducers.
This module is the software fusion layer that turns raw echo timestamps
into classified detections and advisory inputs.

## Status

Scaffold + physics model + 16 unit tests. Real transducer I/O requires
hardware bridge (separate from this repo).

## Why not full bat sonar at highway speed

Bats fly 5-10 m/s. At 27 m/s (60 mph), 10 m of ultrasonic range is
0.37 seconds of reaction time — enough for the last-second swerve or
brake, not for planning. That's exactly why it sits as a near-field
complement to radar, not a replacement.
