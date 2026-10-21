"""Numba version of the 21/70/7 luminance filter.

The math matches src/rgb_filter.py. That module stays the default and
stays importable. Set OMNI_FILTER_BACKEND=numba to select this one.
If Numba is not installed, callers keep the Python filter.
"""
from __future__ import annotations

import numpy as np

try:
    from numba import njit, prange
except ImportError:  # pragma: no cover - exercised only without the package
    njit = None
    prange = range

def _require_numba():
    if njit is None:
        raise RuntimeError(
            "numba is not installed. Keep OMNI_FILTER_BACKEND=python, "
            "or pip install numba."
        )


if njit is not None:
    @njit(cache=True, parallel=True)
    def _filter_numba(src):
        h, w, _ = src.shape
        out = np.empty((h, w), dtype=np.float32)
        w0 = np.float32(0.21)
        w1 = np.float32(0.70)
        w2 = np.float32(0.07)
        for y in prange(h):
            for x in range(w):
                out[y, x] = (
                    src[y, x, 0] * w0
                    + src[y, x, 1] * w1
                    + src[y, x, 2] * w2
                )
        return out
else:
    def _filter_numba(src):  # type: ignore[misc]
        raise RuntimeError("numba is not installed")


def rgb_filter(img: np.ndarray) -> np.ndarray:
    """Weighted luminance on a copy. Does not modify `img`."""
    _require_numba()
    src = np.ascontiguousarray(img, dtype=np.float32)
    return _filter_numba(src)


def benchmark_filter(n_frames: int = 2000, seed: int = 0) -> dict:
    """Time this filter alone, and the original Python filter, on one 1080p frame.

    The frame is built outside the timer, matching benchmark_perf.py,
    which also generates the image before it starts the clock. n_frames
    defaults to 2000, the count used for the published pipeline table.
    The first Numba call is a compile warmup and is not included.
    """
    import time

    from rgb_filter import rgb_filter as python_filter

    rng = np.random.default_rng(seed)
    img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
    python_filter(img)
    rgb_filter(img)

    def _time(fn) -> float:
        t0 = time.perf_counter()
        for _ in range(n_frames):
            fn(img)
        return (time.perf_counter() - t0) / n_frames * 1000.0

    python_ms = _time(python_filter)
    numba_ms = _time(rgb_filter)
    return {
        "frames": n_frames,
        "python_ms": round(python_ms, 3),
        "numba_ms": round(numba_ms, 3),
        "speedup": round(python_ms / numba_ms, 2) if numba_ms else None,
    }
