# Author: Joseph Rocco Peransi
"""Kalman-style sensor fusion from OmniPerceptionDashboard v0.9.4.

Confidence model: base 0.5 + lidar 0.3 + camera 0.15, minus 0.1 if
distance > 100m. Entities filtered to y in (-10, 150).
"""

BASE_CONFIDENCE = 0.5
LIDAR_BOOST = 0.3
CAMERA_BOOST = 0.15
RANGE_PENALTY = 0.1
RANGE_PENALTY_THRESHOLD = 100.0


def fuse_entity(entity: dict, lidar: bool = True, camera: bool = True, radar: bool = True) -> dict:
    """Apply v0.9.4 confidence fusion to one entity."""
    confidence = BASE_CONFIDENCE
    if lidar:
        confidence += LIDAR_BOOST
    if camera:
        confidence += CAMERA_BOOST
    if entity.get("y", 0) > RANGE_PENALTY_THRESHOLD:
        confidence -= RANGE_PENALTY
    entity["confidence"] = min(confidence, 0.999)
    return entity


def fuse_frame(entities: list, lidar: bool = True, camera: bool = True, radar: bool = True) -> list:
    """Fuse all entities and filter to visible range."""
    fused = [fuse_entity(dict(e), lidar, camera, radar) for e in entities]
    return [e for e in fused if -10 < e.get("y", 0) < 150]


if __name__ == "__main__":
    e = {"type": "car", "x": 0, "y": 50}
    print(fuse_entity(e))
    e2 = {"type": "truck", "x": 3.5, "y": 120}
    print(fuse_entity(e2))