"""Temporal persistence filter.

A one-frame shadow or reflection must not reach the HUD. A cluster is
promoted only after 3 consecutive hits. Three missed frames drop it,
and a track older than 10 frames since it was last seen is dropped so
a fast car cannot linger as a false persistent object.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from fast_bev import FastBevLookup

# Rough ground scale when a BEV table is not available.
METERS_PER_PIXEL = 0.05
MATCH_M = 2.0
PROMOTE_HITS = 3
DROP_MISSES = 3
MAX_AGE = 10


@dataclass
class TemporalTrack:
    object_id: int
    hit_count: int
    miss_count: int
    last_seen_frame: int
    centroid: tuple[float, float]  # (x, z) meters. x lateral, z forward.
    hazard_type: str


def _centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    n = float(len(points))
    return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)


def cluster_points(points: list[tuple[float, float]], radius_m: float = MATCH_M) -> list[tuple[float, float]]:
    """Group points within roughly `radius_m` of their cluster centroid."""
    clusters: list[list[tuple[float, float]]] = []
    for p in points:
        placed = False
        for group in clusters:
            cx, cz = _centroid(group)
            if math.hypot(p[0] - cx, p[1] - cz) <= radius_m:
                group.append(p)
                placed = True
                break
        if not placed:
            clusters.append([p])
    return [_centroid(group) for group in clusters]


def project_to_meters(
    points_uv: list[tuple[float, float]],
    bev: FastBevLookup | None = None,
) -> list[tuple[float, float]]:
    """Map image (u, v) outliers into (x, z) meters.

    Uses fast_bev when a lookup is supplied and the pixel is inside it.
    Otherwise scales raw image coordinates by METERS_PER_PIXEL.
    fast_bev returns (forward, lateral); this stores (lateral, forward)
    so x/z match the rest of the engine.
    """
    out: list[tuple[float, float]] = []
    for u, v in points_uv:
        proj = None
        if bev is not None:
            proj = bev.project(int(u), int(v))
        if proj is None:
            out.append((float(u) * METERS_PER_PIXEL, float(v) * METERS_PER_PIXEL))
        else:
            forward_m, lateral_m = proj
            out.append((lateral_m, forward_m))
    return out


@dataclass
class TemporalFilter:
    match_m: float = MATCH_M
    promote_hits: int = PROMOTE_HITS
    drop_misses: int = DROP_MISSES
    max_age: int = MAX_AGE
    tracks: list[TemporalTrack] = field(default_factory=list)
    _next_id: int = 1

    def update(
        self,
        points_m: list[tuple[float, float]],
        frame: int,
        hazard_type: str = "obstacle",
    ) -> list[TemporalTrack]:
        """Ingest one frame of (x, z) meter points. Return confirmed tracks."""
        centroids = cluster_points([(float(p[0]), float(p[1])) for p in points_m], self.match_m)
        matched: set[int] = set()
        for cx, cz in centroids:
            best: TemporalTrack | None = None
            best_d = self.match_m
            for track in self.tracks:
                if track.object_id in matched:
                    continue
                d = math.hypot(cx - track.centroid[0], cz - track.centroid[1])
                if d < best_d:
                    best = track
                    best_d = d
            if best is None:
                born = TemporalTrack(
                    object_id=self._next_id,
                    hit_count=1,
                    miss_count=0,
                    last_seen_frame=frame,
                    centroid=(cx, cz),
                    hazard_type=hazard_type,
                )
                self._next_id += 1
                self.tracks.append(born)
                matched.add(born.object_id)
                continue
            matched.add(best.object_id)
            best.hit_count += 1
            best.miss_count = 0
            best.last_seen_frame = frame
            best.centroid = (cx, cz)
            best.hazard_type = hazard_type

        for track in self.tracks:
            if track.object_id in matched:
                continue
            # Consecutive persistence: a miss breaks the promotion streak.
            track.miss_count += 1
            track.hit_count = 0

        kept: list[TemporalTrack] = []
        for track in self.tracks:
            age = frame - track.last_seen_frame
            if track.miss_count > self.drop_misses:
                continue
            if age >= self.max_age:
                continue
            kept.append(track)
        self.tracks = kept
        return [track for track in self.tracks if track.hit_count >= self.promote_hits]

    def update_image_outliers(
        self,
        points_uv: list[tuple[float, float]],
        frame: int,
        hazard_type: str = "obstacle",
        bev: FastBevLookup | None = None,
    ) -> list[TemporalTrack]:
        return self.update(project_to_meters(points_uv, bev), frame, hazard_type)
