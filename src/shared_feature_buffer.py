"""Shared feature buffer — process visual features once, share via references.

Models the centralized foundation module pattern from the deep dives:
- One backbone pass extracts features (RGB filter + quadrant stats here).
- Downstream heads (RANSAC, fusion, decision) receive a handle, not a copy.
- Avoids the "five chefs chopping the same onion" redundancy.
- In pure Python this is reference sharing; on GPU it becomes zero-copy
  memory handles. The interface is the same.

Isolation note: each head can fail independently. A crash in one head
does not destroy the buffer or the other heads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import copy


@dataclass
class FeatureHandle:
    """Lightweight handle that downstream heads hold instead of raw data."""
    buffer_id: int
    timestamp_ms: int
    feature_keys: List[str]

    def __post_init__(self):
        # Handle is intentionally thin; the buffer owns the data.
        pass


class SharedFeatureBuffer:
    """Central buffer that stores features once and hands out handles.

    Downstream modules call get_handle() and then read via the buffer.
    They never receive a deep copy of the features.
    """

    def __init__(self):
        self._buffer: Dict[str, Any] = {}
        self._timestamp_ms: int = 0
        self._buffer_id: int = 0
        self._heads: Dict[str, bool] = {}  # head_name -> alive

    def process_once(self, raw_frame: Dict[str, Any], timestamp_ms: int) -> FeatureHandle:
        """Single extraction pass. Called once per frame."""
        self._buffer_id += 1
        self._timestamp_ms = timestamp_ms
        # Placeholder extraction: RGB filter stats + quadrant means.
        # Real system would run Dino V2 or equivalent here.
        self._buffer = {
            "rgb_mean": raw_frame.get("rgb_mean", [0.0, 0.0, 0.0]),
            "quadrant_activity": raw_frame.get("quadrant_activity", [0.0] * 4),
            "edge_strength": raw_frame.get("edge_strength", 0.0),
            "timestamp_ms": timestamp_ms,
        }
        return FeatureHandle(
            buffer_id=self._buffer_id,
            timestamp_ms=timestamp_ms,
            feature_keys=list(self._buffer.keys()),
        )

    def read(self, handle: FeatureHandle, key: str) -> Any:
        """Read a feature by key. No copy of the whole buffer."""
        if handle.buffer_id != self._buffer_id:
            raise RuntimeError("Stale handle")
        return self._buffer.get(key)

    def register_head(self, name: str) -> None:
        self._heads[name] = True

    def head_failed(self, name: str) -> None:
        """Mark a head as failed. Buffer and other heads remain intact."""
        self._heads[name] = False

    def alive_heads(self) -> List[str]:
        return [n for n, alive in self._heads.items() if alive]

    def memory_overhead_mb(self) -> float:
        """Rough estimate of isolation overhead (podcast claimed ~214 MB on real hardware)."""
        # Pure Python model: negligible. Real GPU isolation is larger.
        return 0.5


def stopping_distance_saved_m(speed_mph: float, latency_reduction_pct: float = 95.0) -> float:
    """Physical impact of latency cut (podcast claim: 95% -> 4.14 m at 40 mph).

    Simplified model: stopping distance scales with reaction time.
    Base reaction time assumed 200 ms; 95% cut leaves 10 ms.
    """
    speed_mps = speed_mph * 0.44704
    base_reaction_s = 0.200
    reduced_reaction_s = base_reaction_s * (1.0 - latency_reduction_pct / 100.0)
    delta_s = base_reaction_s - reduced_reaction_s
    return speed_mps * delta_s
