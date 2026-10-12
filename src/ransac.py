"""RANSAC inlier/outlier detection.

Fits a model to road samples while rejecting outliers — boulders,
debris, fallen logs. Keeps a single bad frame from poisoning the
perception pipeline.
"""
import numpy as np


def ransac_line(pts: np.ndarray, n_iter: int = 200, thresh: float = 2.0, rng=None):
    """Fit a line to 2D points, rejecting outliers.

    Returns (model (a, b), inlier_mask, outlier_mask).
    """
    if rng is None:
        rng = np.random.default_rng(42)
    best_in, best_model = 0, None
    for _ in range(n_iter):
        i, j = rng.choice(len(pts), 2, replace=False)
        x1, y1 = pts[i]
        x2, y2 = pts[j]
        if abs(x2 - x1) < 1e-9:
            continue
        a = (y2 - y1) / (x2 - x1)
        b = y1 - a * x1
        dist = np.abs(pts[:, 1] - (a * pts[:, 0] + b))
        inl = int(np.sum(dist < thresh))
        if inl > best_in:
            best_in, best_model = inl, (a, b)
    a, b = best_model
    dist = np.abs(pts[:, 1] - (a * pts[:, 0] + b))
    inliers = dist < thresh
    return best_model, inliers, ~inliers


def detect_hazards(gray: np.ndarray, road_y: float = 540.0) -> dict:
    """Scan a grayscale frame for outlier hazards against the road line."""
    H, W = gray.shape
    # sample points along the expected road line
    xs = np.linspace(0, W - 1, 200)
    ys = gray[int(road_y), xs.astype(int)].astype(float)
    pts = np.column_stack([xs, ys])
    model, inl, out = ransac_line(pts)
    outlier_pts = pts[out]
    return {
        "model": model,
        "n_inliers": int(inl.sum()),
        "n_outliers": int(out.sum()),
        "outlier_points": outlier_pts.tolist(),
        "hazard_detected": len(outlier_pts) > 0,
    }