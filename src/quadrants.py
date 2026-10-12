"""Quadrant split: spider-eye sensor architecture.

Each sensor is divided into 4 quadrants so compute is spread
across regions instead of processing one full frame at a time.
Bottom bumper sensors watch the road; upper sensors watch the horizon.
"""
import numpy as np


def split_quadrants(gray: np.ndarray):
    """Split a grayscale frame into 4 quadrants: TL, TR, BL, BR."""
    H, W = gray.shape
    return {
        "TL": gray[: H // 2, : W // 2],
        "TR": gray[: H // 2, W // 2:],
        "BL": gray[H // 2:, : W // 2],
        "BR": gray[H // 2:, W // 2:],
    }


def assign_sensors(quadrants: dict, layout: str = "bumper") -> dict:
    """Assign quadrants to sensor roles.

    bumper: BL/BR watch the road surface, TL/TR watch the horizon.
    """
    if layout == "bumper":
        return {
            "road_left": quadrants["BL"],
            "road_right": quadrants["BR"],
            "horizon_left": quadrants["TL"],
            "horizon_right": quadrants["TR"],
        }
    return quadrants