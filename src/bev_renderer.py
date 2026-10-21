# Author: Joseph Rocco Peransi
"""Top-down BEV canvas renderer from OmniPerceptionDashboard v0.9.4.

World coords: X [-10, 10] meters, Y [0, 100] meters ahead.
Screen: X [0, width], Y [height, 0]. 6 pixels per meter.
Ego vehicle at bottom center, sensor frustum drawn from it.
"""

M_TO_PX = 6
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
VEHICLE_Y_OFFSET = CANVAS_HEIGHT - 100


def to_screen(x: float, y: float, width: int = CANVAS_WIDTH, height: int = CANVAS_HEIGHT) -> tuple:
    """Convert world meters to screen pixels."""
    center_x = width / 2
    sx = center_x + x * M_TO_PX * 4
    sy = (height - 100) - y * M_TO_PX
    return sx, sy


def entity_box(entity: dict) -> dict:
    """Compute screen-space bounding box for an entity."""
    sx, sy = to_screen(entity["x"], entity["y"])
    sw = entity.get("width", 2.0) * M_TO_PX * 4
    sl = entity.get("length", 4.5) * M_TO_PX
    return {"x": sx - sw / 2, "y": sy - sl, "w": sw, "h": sl, "sx": sx, "sy": sy}


def entity_color(entity: dict) -> str:
    """Color per type (from v0.9.4)."""
    return {"pedestrian": "#ef4444", "truck": "#eab308", "car": "#10b981"}.get(
        entity["type"], "#3b82f6"
    )


if __name__ == "__main__":
    e = {"type": "car", "x": 0, "y": 50, "width": 2.0, "length": 4.5}
    b = entity_box(e)
    print(f"Box: x={b['x']:.1f}, y={b['y']:.1f}, w={b['w']:.1f}, h={b['h']:.1f}")
    print(f"Color: {entity_color(e)}")