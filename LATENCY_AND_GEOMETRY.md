# Latency and Geometry Notes (from deep-dive research)

## Shared feature buffer
- Process visual features once per frame; downstream heads receive handles.
- Avoids redundant computation ("five chefs, one onion").
- Process isolation: one head failure does not destroy the buffer or other heads.
- Python model overhead is negligible; real GPU isolation was cited at ~214 MB with 3.3× speedup under TensorRT/CUDA MPS.

## Fast BEV lookup table
- Pre-computed 2D image → BEV (x,y) mapping.
- Eliminates per-frame spherical math and the distortion that comes from flattening a 360° view onto a grid.
- Table for 1280×720 is ~14 MB. Lookup is O(1).
- Cited research: >50 FPS with this approach.

## Stopping-distance impact
- 95% reduction in inter-process communication latency (lock-free shared memory vs serialization) was claimed to save ~4.14 m of stopping distance at 40 mph.
- Model in `shared_feature_buffer.stopping_distance_saved_m()` reproduces that order of magnitude.
- This is the physical safety argument for investing in the communication layer, not just the detector.

## What is not yet implemented
- Real GPU zero-copy / TensorRT / CUDA MPS (requires hardware).
- Full spherical manifold convolution (lookup table is the fast approximation).
- Omnimodal world-model / reverse-diffusion prediction (verification problem remains open).

## Status
Scaffold + unit tests. Ready to wire into the integrated pipeline and dashboard renderer.
