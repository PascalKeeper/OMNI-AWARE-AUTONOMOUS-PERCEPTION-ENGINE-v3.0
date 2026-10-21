# Author: Joseph Rocco Peransi
"""CPU-bound color spectrum lock from OmniAware v1.2.0-GOLD.

Raw pixel manipulation bypassing the GPU bus.
Red 70%, Green 70%, Blue 7%.
"""

RED_LOCK = 0.70
GREEN_LOCK = 0.70
BLUE_LOCK = 0.07


def apply_spectrum_lock(r: float, g: float, b: float) -> tuple:
    """Apply the v1.2.0 spectrum lock to a single RGB pixel."""
    return (r * RED_LOCK, g * GREEN_LOCK, b * BLUE_LOCK)


def apply_spectrum_lock_frame(pixels: list) -> list:
    """Apply spectrum lock to a list of (r, g, b) tuples."""
    return [apply_spectrum_lock(r, g, b) for r, g, b in pixels]


if __name__ == "__main__":
    print(apply_spectrum_lock(1.0, 1.0, 1.0))  # (0.70, 0.70, 0.07)