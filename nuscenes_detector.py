"""Bridge from one adapter frame to the OMNI-AWARE perception modules.

The benchmark calls detect(frame). The frame's front image is run through
the RGB filter, the quadrant split, and RANSAC. Sensor fusion supplies
the confidence, and predictive braking is evaluated on the same entities.

src/pipeline.py does not read lidar point clouds. sensor_fusion only
range-gates a distance, so lidar is not a second detection source.

RANSAC here fits luminance along one road-quadrant scanline. Outlier
clusters are placed on the ground plane with a fixed CAM_FRONT model so
they share the adapter's ego frame (x forward, y left, z up). That model
is not fit to the labels.
"""
import logging
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

log = logging.getLogger("nuscenes_detector")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

# Fixed front-camera model. nuScenes ego origin is the rear axle.
# Intrinsics are the published CAM_FRONT values used across the mini logs;
# the extrinsic is the typical bumper mount, not a per-scene calibration.
FX = 1266.417203046554
FY = 1266.417203046554
CX = 816.2670197447984
CY = 491.50706579294757
CAM_X = 1.70
CAM_Y = 0.015
CAM_Z = 1.51

_MODULES = None
_IMPORT_ERROR = None
_LIDAR_NOTE_EMITTED = False


def _load_modules():
    """Import the pipeline pieces once. Later frames reuse the result."""
    global _MODULES, _IMPORT_ERROR
    if _MODULES is not None or _IMPORT_ERROR is not None:
        return _MODULES
    try:
        from rgb_filter import rgb_filter
        from quadrants import assign_sensors, split_quadrants
        from ransac import ransac_line
        from sensor_fusion import fuse_frame
        from predictive_braking import should_brake
        from shared_feature_buffer import SharedFeatureBuffer
    except Exception as exc:
        _IMPORT_ERROR = exc
        log.error("module import failed: %s: %s", type(exc).__name__, exc)
        return None
    buffer = SharedFeatureBuffer()
    buffer.register_head("ransac")
    buffer.register_head("fusion")
    _MODULES = {
        "rgb_filter": rgb_filter,
        "split_quadrants": split_quadrants,
        "assign_sensors": assign_sensors,
        "ransac_line": ransac_line,
        "fuse_frame": fuse_frame,
        "should_brake": should_brake,
        "buffer": buffer,
    }
    return _MODULES


def _read_image(path: str):
    """Load a front-camera frame as float RGB. None if it cannot be read."""
    try:
        import cv2
    except Exception as exc:
        log.error("cv2 import failed: %s: %s", type(exc).__name__, exc)
        return None
    bgr = cv2.imread(path, cv2.IMREAD_COLOR)
    if bgr is None:
        return None
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return rgb.astype(np.float32)


def _scanline_outliers(ransac_line, road: np.ndarray):
    """Outlier pixel columns on the middle row of one road quadrant."""
    height, width = road.shape
    if height < 1 or width < 2:
        return [], 0, 0
    xs = np.linspace(0, width - 1, 100)
    row = road[height // 2, xs.astype(int)].astype(float)
    pts = np.column_stack([xs, row])
    try:
        _model, _inliers, outliers = ransac_line(pts)
    except Exception as exc:
        log.error("ransac failed: %s: %s", type(exc).__name__, exc)
        return [], 0, int(len(xs))
    mask = np.asarray(outliers, dtype=bool)
    return xs[mask], int(mask.sum()), int(len(xs))


def _cluster_columns(columns, gap: float):
    """Mean column of each run of nearby outlier samples."""
    if len(columns) == 0:
        return []
    ordered = np.sort(np.asarray(columns, dtype=float))
    groups = [[ordered[0]]]
    for value in ordered[1:]:
        if value - groups[-1][-1] <= gap:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [float(np.mean(group)) for group in groups]


def _ground_point(u: float, v: float):
    """Intersect a pixel ray with the ground in the ego frame.

    Returns (x_forward, y_left, z_up) or None when the pixel is at or
    above the horizon.
    """
    if v <= CY:
        return None
    depth = CAM_Z * FY / (v - CY)
    if not np.isfinite(depth) or depth <= 0.5 or depth > 300.0:
        return None
    x_cam = (u - CX) * depth / FX
    ego_x = CAM_X + depth
    ego_y = CAM_Y - x_cam
    return float(ego_x), float(ego_y), 0.0


def _note_lidar(frame):
    """Say once that the pipeline cannot consume the lidar sweep."""
    global _LIDAR_NOTE_EMITTED
    if _LIDAR_NOTE_EMITTED:
        return
    _LIDAR_NOTE_EMITTED = True
    path = frame.get("lidar_path")
    log.info(
        "pipeline has no lidar point-cloud detector; sensor_fusion only "
        "range-gates a distance. lidar_path=%s exists=%s",
        path,
        bool(path) and os.path.isfile(path),
    )


def detect(frame: dict) -> list:
    """Detections for one frame. An import or runtime failure returns []."""
    detect.frame_stats = {"outlier_points": 0, "scan_points": 0, "outlier_fraction": None}
    modules = _load_modules()
    if modules is None:
        return []
    try:
        _note_lidar(frame)
        image = _read_image(frame["image_path"])
        if image is None:
            log.error("front camera image unreadable: %s", frame.get("image_path"))
            return []
        gray = modules["rgb_filter"](image)
        quadrants = modules["split_quadrants"](gray)
        sensors = modules["assign_sensors"](quadrants)
        # One extraction. RANSAC and fusion read this handle, not a second filter pass.
        buffer = modules["buffer"]
        handle = buffer.process_once(
            {
                "rgb_mean": [float(image[..., c].mean()) for c in range(image.shape[2])],
                "quadrant_activity": [float(np.mean(q)) for q in quadrants.values()],
                "edge_strength": float(np.mean(np.abs(np.diff(gray, axis=1)))) if gray.shape[1] > 1 else 0.0,
                "gray": gray,
                "sensors": sensors,
            },
            timestamp_ms=int(frame.get("timestamp") or 0) // 1000,
        )
        gray = buffer.read(handle, "gray")
        sensors = buffer.read(handle, "sensors")
        full_h, full_w = gray.shape
        entities = []
        outlier_points = 0
        scan_points = 0
        for name in ("road_left", "road_right"):
            road = sensors[name]
            columns, n_out, n_pts = _scanline_outliers(modules["ransac_line"], road)
            outlier_points += n_out
            scan_points += n_pts
            if len(columns) == 0:
                continue
            spacing = max((road.shape[1] - 1) / 99.0, 1.0)
            local_row = road.shape[0] // 2
            global_row = full_h // 2 + local_row
            origin = full_w // 2 if name == "road_right" else 0
            for local_u in _cluster_columns(columns, gap=2.0 * spacing):
                point = _ground_point(origin + local_u, global_row)
                if point is None:
                    continue
                ego_x, ego_y, ego_z = point
                entities.append(
                    {
                        "type": "obstacle",
                        "x": ego_y,  # fusion / braking: lateral
                        "z": ego_x,  # fusion / braking: forward range
                        "ego_x": ego_x,
                        "ego_y": ego_y,
                        "ego_z": ego_z,
                        "width": 1.0,
                        "height": 1.0,
                    }
                )
        fused = modules["fuse_frame"](entities)
        modules["should_brake"](fused)
        detections = []
        for ent in fused:
            forward = float(ent["ego_x"])
            lateral = float(ent["ego_y"])
            detections.append(
                {
                    "type": "obstacle",
                    "x": forward,
                    "y": lateral,
                    "z": float(ent["ego_z"]),
                    "confidence": float(ent.get("confidence", 0.0)),
                    "distance": float(np.hypot(forward, lateral)),
                }
            )
        detect.frame_stats = {
            "outlier_points": outlier_points,
            "scan_points": scan_points,
            "outlier_fraction": (outlier_points / scan_points) if scan_points else None,
        }
        return detections
    except Exception as exc:
        log.error(
            "detection failed for %s: %s: %s",
            frame.get("sample_token", frame.get("image_path")),
            type(exc).__name__,
            exc,
        )
        return []
