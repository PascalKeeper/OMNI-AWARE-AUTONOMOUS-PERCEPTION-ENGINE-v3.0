# Author: Joseph Rocco Peransi
"""RGB filter: 21% red, 70% green, 7% blue.

Reduces image data 3x by collapsing RGB to a single luminance channel.
Green-weighted because it carries most of the luminance detail.

Color-critical signals must never be read from the filtered buffer.
Brake-light red and signal yellow live only in the original RGB frame
(or the copy returned by preserve_color). The 21/70/7 weights run on
a separate grayscale buffer and do not modify the caller's image.
A bright red brake light (255, 0, 0) collapses to about 54 in gray,
which is no longer distinguishable from a dim neutral pixel.
"""
import numpy as np

WEIGHTS = np.array([0.21, 0.70, 0.07], dtype=np.float32)


def preserve_color(img: np.ndarray) -> np.ndarray:
    """Return an untouched RGB copy for brake lights and turn signals."""
    return np.array(img, copy=True)


def rgb_filter(img: np.ndarray) -> np.ndarray:
    """Apply weighted luminance on a separate buffer. (H, W, 3) -> (H, W).

    Does not write into `img`. The result has no color channels.
    """
    src = np.array(img, dtype=np.float32, copy=True)
    return src @ WEIGHTS


def rgb_filter_uint8(img: np.ndarray) -> np.ndarray:
    """Same filter, returns uint8 for display/thresholding."""
    return rgb_filter(img).clip(0, 255).astype(np.uint8)