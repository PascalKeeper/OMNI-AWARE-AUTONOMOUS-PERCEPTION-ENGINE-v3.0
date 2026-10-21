"""Spectrum isolation: brake-light red survives only on the preserved RGB copy."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rgb_filter import rgb_filter, preserve_color
from ransac import detect_color_hazards


def test_brake_light_survives_on_color_copy():
    img = np.zeros((32, 32, 3), dtype=np.float32)
    img[8:20, 8:24, 0] = 255  # bright red rectangle
    original = img.copy()
    color = preserve_color(img)
    gray = rgb_filter(img)

    assert np.array_equal(img, original)
    assert not np.shares_memory(color, img)
    assert gray.ndim == 2

    red_gray = float(gray[12, 16])
    assert abs(red_gray - 255.0 * 0.21) < 0.2
    assert red_gray < 255.0 * 0.3

    found = detect_color_hazards(color)
    assert found["brake_light"]
    assert found["n_brake_px"] == 12 * 16
    assert not found["signal_yellow"]

    try:
        detect_color_hazards(gray)
        raise AssertionError("grayscale buffer must not be accepted as a color path")
    except ValueError:
        pass


if __name__ == "__main__":
    test_brake_light_survives_on_color_copy()
    print("spectrum isolation tests passed")
