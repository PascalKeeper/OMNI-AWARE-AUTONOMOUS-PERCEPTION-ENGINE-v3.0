# Author: Joseph Rocco Peransi
"""Canvas renderer: perspective projection driving view.

Ported from OmniAwareDashboard v1.0.4 (Nov 2025).
Pure-Python reference implementation of the v1 canvas draw logic.
For the browser, the original React/canvas code remains the source of truth;
this module mirrors its math for testing and headless rendering.
"""
import math

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 500


def project(entity: dict, horizon_y: float = CANVAS_HEIGHT * 0.4) -> dict:
    """Project an entity (x in -100..100, z in 0..200) onto canvas coords."""
    pf = 1 - (entity["z"] / 200)  # projection factor
    draw_y = horizon_y + pf * (CANVAS_HEIGHT - horizon_y)
    draw_x = CANVAS_WIDTH / 2 + entity["x"] * pf * 4
    draw_w = entity["width"] * 20 * pf
    draw_h = entity["height"] * 20 * pf
    return {"x": draw_x, "y": draw_y, "w": draw_w, "h": draw_h}


def entity_color(entity: dict) -> str:
    """Color per entity type (from v1.0.4)."""
    return {"CAR": "#34d399", "PEDESTRIAN": "#fbbf24", "OBSTACLE": "#f87171"}.get(
        entity["type"], "#38bdf8"
    )


if __name__ == "__main__":
    e = {"type": "CAR", "x": 0, "z": 100, "width": 2.5, "height": 2}
    p = project(e)
    print(f"Projected: x={p['x']:.1f}, y={p['y']:.1f}, w={p['w']:.1f}, h={p['h']:.1f}")