"""Numba luminance filter matches the Python 21/70/7 filter."""
import os
import sys
import types

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import rgb_filter as python_filter
from rgb_filter_numba import rgb_filter as numba_filter
from pipeline import active_rgb_filter


def test_numba_matches_python_within_tolerance():
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, size=(48, 64, 3)).astype(np.float32)
    img[0, 0] = (255, 0, 0)
    img[1, 1] = (10, 200, 30)
    original = img.copy()
    python_out = python_filter.rgb_filter(img)
    numba_out = numba_filter(img)
    assert np.array_equal(img, original)
    assert python_out.shape == numba_out.shape
    assert float(np.max(np.abs(python_out - numba_out))) < 1e-5


def test_default_backend_is_python():
    os.environ.pop("OMNI_FILTER_BACKEND", None)
    assert active_rgb_filter() is python_filter.rgb_filter


def test_numba_backend_selects_compiled_filter():
    os.environ["OMNI_FILTER_BACKEND"] = "numba"
    try:
        assert active_rgb_filter() is numba_filter
    finally:
        os.environ.pop("OMNI_FILTER_BACKEND", None)


def test_missing_numba_falls_back_to_python():
    saved = sys.modules.get("rgb_filter_numba")
    sys.modules["rgb_filter_numba"] = types.ModuleType("rgb_filter_numba")
    os.environ["OMNI_FILTER_BACKEND"] = "numba"
    try:
        assert active_rgb_filter() is python_filter.rgb_filter
    finally:
        os.environ.pop("OMNI_FILTER_BACKEND", None)
        if saved is None:
            sys.modules.pop("rgb_filter_numba", None)
        else:
            sys.modules["rgb_filter_numba"] = saved


def test_unknown_backend_stays_python():
    os.environ["OMNI_FILTER_BACKEND"] = "cuda"
    try:
        assert active_rgb_filter() is python_filter.rgb_filter
    finally:
        os.environ.pop("OMNI_FILTER_BACKEND", None)


if __name__ == "__main__":
    test_numba_matches_python_within_tolerance()
    test_default_backend_is_python()
    test_numba_backend_selects_compiled_filter()
    test_missing_numba_falls_back_to_python()
    test_unknown_backend_stays_python()
    print("numba rgb filter tests passed")
