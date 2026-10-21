# Author: Joseph Rocco Peransi
"""Fast BEV lookup-table path — pre-computed 2D-to-3D mapping.

Avoids the "flatten the globe and Antarctica looks huge" distortion
problem. Instead of computing spherical projections every frame, we
build a lookup table once and index into it.

Podcast claim: >50 FPS with pre-computed tables. This module models
that pattern so the dashboard / HUD can use it without per-frame math.
"""

from __future__ import annotations

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BevPoint:
    u: int  # image column
    v: int  # image row
    x: float  # BEV meters forward
    y: float  # BEV meters lateral


class FastBevLookup:
    """Pre-computed lookup from image (u,v) to BEV (x,y).

    Built once at init. Per-frame projection is a table lookup.
    """

    def __init__(self, image_w: int = 1280, image_h: int = 720,
                 fov_deg: float = 90.0, max_range_m: float = 100.0,
                 grid_step_m: float = 0.5):
        self.image_w = image_w
        self.image_h = image_h
        self.fov_deg = fov_deg
        self.max_range_m = max_range_m
        self.grid_step_m = grid_step_m
        self._table: List[Optional[Tuple[float, float]]] = [None] * (image_w * image_h)
        self._build()

    def _build(self) -> None:
        """One-time table construction."""
        half_fov = math.radians(self.fov_deg / 2.0)
        for v in range(self.image_h):
            # Simple linear model: bottom of image = near, top = far
            # Real spherical manifold would use proper projection math.
            range_frac = 1.0 - (v / self.image_h)
            range_m = range_frac * self.max_range_m
            for u in range(self.image_w):
                # Lateral: center of image = 0, edges = ±tan(half_fov)*range
                u_frac = (u / self.image_w) - 0.5
                lateral_m = u_frac * 2.0 * math.tan(half_fov) * range_m
                idx = v * self.image_w + u
                self._table[idx] = (range_m, lateral_m)

    def project(self, u: int, v: int) -> Optional[Tuple[float, float]]:
        """O(1) lookup. Returns (x_forward_m, y_lateral_m) or None."""
        if not (0 <= u < self.image_w and 0 <= v < self.image_h):
            return None
        return self._table[v * self.image_w + u]

    def project_batch(self, points: List[Tuple[int, int]]) -> List[Optional[Tuple[float, float]]]:
        return [self.project(u, v) for u, v in points]

    def table_size_mb(self) -> float:
        # 1280*720 * 16 bytes ≈ 14 MB
        return (self.image_w * self.image_h * 16) / (1024 * 1024)

    def fps_estimate(self, points_per_frame: int = 10000) -> float:
        """Rough FPS if lookup is the bottleneck (pure Python)."""
        # Real GPU table would be far higher; this is a model.
        lookups_per_ms = 50000  # conservative Python estimate
        ms = points_per_frame / lookups_per_ms
        return 1000.0 / max(ms, 0.01)
