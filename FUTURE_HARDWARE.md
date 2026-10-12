# Future Hardware Proposals

Ideas for Tesla sensor suite improvements. None are current fleet capabilities.

## 1. UV Fluorescence Sensing for Night Vision

### The Problem

At night, pedestrians wearing dark clothing against dark backgrounds
are nearly invisible to visible-light cameras. Tesla's raw photon-count
approach helps, but it still depends on visible photons being present.

### The Proposal

Add a UV illuminator (around 365 nm) paired with a camera sensor
without an infrared cut filter. Fluorescent materials in clothing,
shoes, and accessories absorb UV and re-emit visible light, creating
a bright signature against an otherwise black scene.

### Why It Works

- Fluorescence is an active emission, not passive reflection —
  it doesn't require ambient light
- The UV source is invisible to the human eye, so it doesn't
  blind oncoming drivers
- CMOS sensors are naturally sensitive to UV; removing the IR cut
  filter (or adding a UV-pass filter) makes them usable
- Existing Tesla photon-count pipeline could ingest the fluorescence
  channel as an additional data stream

### Challenges

- UV illuminators add cost, power draw, and regulatory questions
  (eye safety at close range)
- Fluorescence varies wildly by clothing material — cotton and
  polyester fluoresce differently than wool or leather
- False positives: many surfaces fluoresce under UV (paper, certain
  plastics, detergents), so the neural net would need training to
  distinguish clothing from background clutter
- Range is limited by UV absorption in air and the inverse-square
  law on the emitted visible light

### Status

Proposal only. Not implemented. Would require hardware changes
that cannot be delivered via OTA.

## 2. Related Ideas (Noted, Not Detailed)

- Active IR illumination for low-light (already partially addressed
  by raw photon counting)
- Polarizing filters to cut glare from wet roads
- Multi-spectral sensors for material classification (metal vs.
  plastic vs. fabric) to improve hazard detection
