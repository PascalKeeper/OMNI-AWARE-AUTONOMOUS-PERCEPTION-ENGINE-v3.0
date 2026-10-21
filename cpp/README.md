# OMNI-AWARE C++ Reference Port
Author: Joseph Rocco Peransi

## What This Is

A single-file C++17 translation of the Python OMNI-AWARE v3.1 pipeline.
It is a **reference implementation** for study and demonstration - NOT
production Tesla code. Tesla's FSD stack is proprietary and runs on
their own silicon (HW3/HW4) with custom CUDA-like kernels.

## Why C++ Matters for the Pitch

1. **No Python runtime.** Tesla vehicles don't ship Python. A C++ port
   proves the algorithms are language-agnostic and portable.
2. **NEON SIMD on ARM.** HW4 uses ARM Cortex cores. C++ with NEON
   intrinsics can vectorize the RGB filter 4-16x over scalar code.
3. **Memory-bandwidth bound, not compute bound.** 1080p RGB is ~6 MB.
   At HW4's ~100 GB/s bandwidth, the filter read alone is <0.1 ms.
   The Python 8.1 ms was interpreter overhead, not algorithm cost.
4. **Deterministic, no GIL.** Real-time systems need predictable latency.
   C++ gives you that; Python's GIL doesn't.

## Build

```bash
mkdir build && cd build
 cmake .. && make
./omni_aware
```

Cross-compile for aarch64 (HW4-like):

```bash
mkdir build-arm && cd build-arm
 cmake -DCMAKE_CXX_FLAGS="-march=armv8-a" -DCMAKE_SYSTEM_NAME=Linux \
      -DCMAKE_SYSTEM_PROCESSOR=aarch64 ..
 make
```

## Expected Performance

| Environment | Filter | Full Pipeline | FPS |
|-------------|--------|---------------|-----|
| Python (measured) | 8.1 ms | ~14 ms | 82 |
| C++ scalar (est.) | ~0.4 ms | ~6 ms | ~160 |
| C++ NEON (est.) | ~0.1 ms | ~2 ms | ~500 |
| HW4 ISP + NEON (est.) | <0.05 ms | <1 ms | 1000+ |

The 422 FPS target becomes reachable on real hardware. The Python
number was never the algorithm's ceiling - it was the interpreter's.

## Honest Caveats

- These are estimates from the mock benchmark, not HW4 measurements.
- Tesla's production stack uses proprietary kernels we cannot replicate.
- The C++ port validates algorithm portability, not vehicle integration.
- No actuation authority. Advisory layer only.

## What's Ported

- RGB filter (21/70/7)
- Quadrant split
- RANSAC road fit
- Sensor fusion (staged ranges: radar 150, camera 120, lidar 80)
- Predictive braking (20 m threshold)
- Map-aware speed advisory (curvature, sight distance, crosswalks,
  school zones, construction)
- Traction loop (grip, wetness, three-signal surface agreement)
- Acoustic classification (gravel hiss, water rumble, dry hum)
