# Safety Validation — OMNI-AWARE v3.0

This directory contains the safety analysis for the OMNI-AWARE perception engine.

## Ablation Study

`ablation_study.py` proves the v1.2.0 CPU spectrum lock destroys color-critical
signals. Run it with:

```
python safety/ablation_study.py
```

Expected output: high chroma loss percentages on brake lights, traffic signals,
and lane markings — demonstrating why this filter cannot be used on real camera feeds.

## Production Checklist

`production_checklist.md` lists everything that must be validated before any
real-vehicle deployment. Most items are unchecked — this is a research project.

## Key Finding

The spectrum lock is the single most dangerous component in the codebase for
production use. It is retained for historical reference only.

All other components (sensor fusion, predictive braking, RANSAC, physics kernel,
decision engine) are sound in principle but unvalidated on real data.