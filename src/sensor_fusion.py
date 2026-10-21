# Author: Joseph Rocco Peransi
"""Sensor fusion: staged detection ranges per sensor type.

Ported from OmniAwareDashboard v1.0.4 (Nov 2025).
Radar detects first at 150m, camera at 120m, lidar at 80m.
Confidence climbs as sensors stack: sensors.length * 0.3 + 100/(z+1) * 0.1.
"""
import numpy as np

# Detection ranges in meters (from v1.0.4)
RADAR_RANGE = 150.0
CAMERA_RANGE = 120.0
LIDAR_RANGE = 80.0

# Confidence weights (from v1.0.4)
SENSOR_CONF_WEIGHT = 0.3
RANGE_CONF_WEIGHT = 0.1


def detect_sensors(z: float) -> list:
    """Return which sensors can see an entity at distance z."""
    sensors = []
    if z < RADAR_RANGE:
        sensors.append("RADAR")
    if z < CAMERA_RANGE:
        sensors.append("CAMERA")
    if z < LIDAR_RANGE:
        sensors.append("LIDAR")
    return sensors


def compute_confidence(z: float, sensors: list = None) -> float:
    """Confidence model from v1.0.4: sensors * 0.3 + 100/(z+1) * 0.1."""
    if sensors is None:
        sensors = detect_sensors(z)
    return min(0.99, len(sensors) * SENSOR_CONF_WEIGHT + (100 / (z + 1)) * RANGE_CONF_WEIGHT)


def fuse_entity(entity: dict) -> dict:
    """Apply sensor fusion to a single entity dict with 'z' key."""
    z = entity["z"]
    sensors = detect_sensors(z)
    entity["detected_by"] = sensors
    entity["confidence"] = compute_confidence(z, sensors)
    return entity


def fuse_frame(entities: list) -> list:
    """Apply sensor fusion to all entities in a frame."""
    return [fuse_entity(dict(e)) for e in entities]


if __name__ == "__main__":
    # sanity check against v1.0.4 behavior
    for z in (200, 150, 120, 80, 20, 5):
        s = detect_sensors(z)
        c = compute_confidence(z, s)
        print(f"z={z:>5}m  sensors={s}  confidence={c:.2f}")