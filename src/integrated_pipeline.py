"""Integrated OMNI-AWARE pipeline v3.1.

Per-frame order: RGB filter -> quadrants -> RANSAC -> sensor fusion ->
predictive braking -> map context -> traction loop -> Wi-Fi shadow layer ->
integrated speed advisory -> decision.

The speed advisory combines three independent risk inputs:
1. Map geometry (curvature, sight distance) via map_advisory_speed
2. Traction state (grip, wetness) via traction_speed_factor
3. RF shadow density (non-line-of-sight occupancy) via shadow reductions

Reduction policy:
- High RF shadow density (>30% of surveyed paths): 50% speed cut
- Any RF shadow detected: 25% speed cut
- Grip below 0.6: 30% cut
- Wetness above 0.5: 15% cut
- Map curvature/sight risk: continuous penalty
- Floor: 5 km/h minimum advisory
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# --- Wi-Fi shadow layer (from wifi_shadow.py) ---

@dataclass
class ShadowDetection:
    bearing_deg: float
    distance_m: float
    confidence: float
    source: str
    estimated_size_m: float
    timestamp_ms: int


@dataclass
class WifiShadowState:
    detections: List[ShadowDetection] = field(default_factory=list)
    ap_count: int = 0
    beacon_count: int = 0
    mean_rssi_dbm: float = 0.0
    shadow_density: float = 0.0
    advisory: Optional[str] = None


# --- Traction layer (from traction_loop.py) ---

def traction_speed_factor(grip: float, wetness: float) -> float:
    """Speed multiplier from tire/surface state."""
    f = 1.0
    if grip < 0.6:
        f *= 0.7
    if wetness > 0.5:
        f *= 0.85
    return f


# --- Map layer (from map_context.py) ---

def map_advisory_speed(base_speed_kmh: float, curvature: float, sight_m: float) -> float:
    """Max safe speed for upcoming geometry.

    Curvature penalty scales with curvature squared relative to sight distance.
    A sharp turn (0.5) at 30 m sight costs roughly half the base speed.
    """
    risk = (curvature ** 2) * 150 / (sight_m + 1)
    return base_speed_kmh / (1 + risk)


# --- Integrated advisory ---

def integrated_speed_advisory(
    base_speed: float,
    grip: float,
    wetness: float,
    curvature: float,
    sight_m: float,
    shadow_state: WifiShadowState,
) -> float:
    """Combine map, traction, and RF shadow into one speed recommendation."""
    speed = map_advisory_speed(base_speed, curvature, sight_m)
    speed *= traction_speed_factor(grip, wetness)
    if shadow_state.shadow_density > 0.3:
        speed *= 0.5
    elif len(shadow_state.detections) > 0:
        speed *= 0.75
    return max(speed, 5.0)


# --- Frame runner ---

@dataclass
class PipelineFrame:
    """One integrated pipeline frame with all layer outputs."""
    base_speed: float
    grip: float
    wetness: float
    curvature: float
    sight_m: float
    shadow_state: WifiShadowState
    advisory_speed: float = 0.0
    advisories: List[str] = field(default_factory=list)

    def run(self) -> float:
        self.advisory_speed = integrated_speed_advisory(
            self.base_speed, self.grip, self.wetness,
            self.curvature, self.sight_m, self.shadow_state,
        )
        if self.shadow_state.advisory:
            self.advisories.append(self.shadow_state.advisory)
        if self.grip < 0.6:
            self.advisories.append(f"Low grip {self.grip:.2f} - traction cut applied.")
        if self.wetness > 0.5:
            self.advisories.append(f"Wetness {self.wetness:.2f} - surface cut applied.")
        if self.curvature > 0.3 and self.sight_m < 50:
            self.advisories.append(
                f"Sharp geometry (curv {self.curvature:.2f}, sight {self.sight_m:.0f}m) - map cut applied."
            )
        return self.advisory_speed
