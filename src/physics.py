# Author: Joseph Rocco Peransi
"""Physics kernel: forward simulation of falling objects.

Predicts where a falling object (log, boulder, debris) lands and
where the vehicle will be at impact — giving a heads-up on
evasive direction.
"""
import numpy as np


def simulate_falling_object(
    v_truck: float = 25.0,
    v_object: float = 25.0,
    height: float = 1.2,
    g: float = 9.81,
    dt: float = 0.001,
    drop_x: float = -10.0,
):
    """Simulate an object falling from a truck.

    Truck at x=0 moving +x. Object drops from truck rear.
    Returns (time_to_impact, object_x, truck_x, gap).
    """
    x_obj, y_obj = drop_x, height
    vx, vy = v_object, 0.0
    t = 0.0
    while y_obj > 0:
        vy -= g * dt
        x_obj += vx * dt
        y_obj += vy * dt
        t += dt
    x_truck = v_truck * t
    return t, x_obj, x_truck, x_obj - x_truck


def predict_evasion(gap: float, v_truck: float = 25.0) -> str:
    """Decide evasive direction from the impact gap."""
    if gap < -5:
        return "veer left"
    if gap > 5:
        return "veer right"
    return "brake — object lands in path"