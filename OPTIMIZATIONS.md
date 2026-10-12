# Performance Analysis and Optimization Roadmap

## Measured Results (CPU, Python, no GPU)

Full pipeline benchmark, 2000 frames, 1080p input:

| Statistic | ms/frame | FPS |
|-----------|-----------|-----|
| Mean | 14.1 | 82 |
| Median | 16.7 | 60 |
| p99 | 22.8 | 44 |
| Best case | 7.8 | 128 |

The original README claimed **422 FPS** (2.37 ms/frame). The real
pipeline is approximately **6x slower** than claimed.

## Bottleneck Breakdown

| Component | ms | % of frame |
|-----------|-----|------------|
| RGB filter (per-pixel loop) | 8.1 | 58% |
| RANSAC (50 iterations) | ~5 | 35% |
| Quadrants + fusion + braking | <0.1 | <1% |

The RGB filter's per-pixel Python loop is the dominant cost. Every
other component is negligible by comparison.

## Optimization Roadmap (in priority order)

### 1. Compile the filter (Numba or Cython) - expected 10-50x

The filter is a simple weighted sum per pixel. Numba's `@njit`
decorator or a Cython extension would compile it to machine code.
Estimated result: filter drops from 8.1 ms to under 0.5 ms,
pushing total frame time toward 6 ms (~170 FPS).

### 2. Replace RANSAC with a fixed road model - expected 2-3x

RANSAC's 50 random iterations are expensive for a problem with a
known structure: the road is a plane converging to a horizon.
A homography or fixed vanishing-point model eliminates the search.
Estimated result: RANSAC cost drops from ~5 ms to ~1 ms.

### 3. Process quadrants independently at lower resolution

Each quadrant is 25% of the frame. Running the filter and RANSAC
on 540x960 quadrants instead of the full 1080p frame cuts pixel
count by 4x for the heavy path.

### 4. Downsample input before filtering

If 1080p isn't required for detection, 720p or 540p input
reduces the filter's pixel count proportionally.

### Combined estimate

Filter (0.5 ms) + RANSAC (1 ms) + rest (<0.1 ms) = ~1.6 ms/frame
= **~600+ FPS**, which would finally beat the 422 claim.

## Honest Framing for the Pitch

The 422 FPS number was a design target, not a measurement. The
measured baseline is 82 FPS mean. The optimization roadmap shows
a credible path to 600+ FPS, but those numbers are estimates until
benchmarked. Present it as: "baseline measured, target defined,
path documented" - not "422 FPS achieved."
