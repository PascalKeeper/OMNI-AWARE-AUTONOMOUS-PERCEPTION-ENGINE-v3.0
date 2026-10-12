"""RGB filter: 21% red, 70% green, 7% blue.

Reduces image data 3x by collapsing RGB to a single luminance channel.
Green-weighted because it carries most of the luminance detail.
"""
import numpy as np

WEIGHTS = np.array([0.21, 0.70, 0.07], dtype=np.float32)


def rgb_filter(img: np.ndarray) -> np.ndarray:
    """Apply weighted luminance filter. (H, W, 3) -> (H, W)."""
    return img @ WEIGHTS


def rgb_filter_uint8(img: np.ndarray) -> np.ndarray:
    """Same filter, returns uint8 for display/thresholding."""
    return (rgb_filter(img.astype(np.float32))).clip(0, 255).astype(np.uint8)