"""Map-aware prediction layer.

Gives the perception engine context beyond line-of-sight: upcoming turns,
alleyways, driveways, crosswalks, school zones, construction. Sensors see
what's in front of them NOW; the map sees the next 200-500 meters.

Backend: simulated map data for now. Real integration would use OSRM
(open-source routing) or OpenStreetMap Overpass API for geometry.
"""
import math


class MapContext:
    """Simulated map provider. In production, backed by OSRM/OSM."""

    def __init__(self):
        # Simulated route: each entry is a segment ahead
        self.segments = [
            {"type": "straight", "length_m": 200, "curvature_deg_per_m": 0.0,
             "speed_limit_kmh": 60, "driveways": 2, "crosswalks": 0,
             "school_zone": False, "construction": False},
            {"type": "right_turn", "length_m": 80, "curvature_deg_per_m": 12.0,
             "speed_limit_kmh": 40, "driveways": 1, "crosswalks": 1,
             "school_zone": False, "construction": False, "sight_distance_m": 80},
            {"type": "alleyway", "length_m": 25, "curvature_deg_per_m": 8.0,
             "speed_limit_kmh": 30, "driveways": 3, "crosswalks": 0,
             "school_zone": False, "construction": False, "sight_distance_m": 25},
            {"type": "straight", "length_m": 300, "curvature_deg_per_m": 1.0,
             "speed_limit_kmh": 50, "driveways": 4, "crosswalks": 1,
             "school_zone": True, "construction": False},
        ]
        self.position_m = 0.0

    def advance(self, distance_m: float):
        """Move along the route."""
        self.position_m += distance_m

    def upcoming(self, horizon_m: float = 200.0) -> list:
        """Return segments within horizon_m ahead."""
        results = []
        pos = self.position_m
        for seg in self.segments:
            seg_start = pos
            seg_end = pos + seg["length_m"]
            if seg_start < self.position_m + horizon_m:
                results.append({**seg, "distance_ahead_m": seg_start - self.position_m})
            pos = seg_end
        return results


def turn_risk(curvature_deg_per_m: float, speed_ms: float, sight_distance_m: float) -> float:
    """Risk score for an upcoming turn.

    Lateral acceleration if taken at current speed, divided by time-to-turn.
    High lateral acc + short sight window = high risk.
    """
    lat_acc = (speed_ms ** 2) * math.radians(curvature_deg_per_m) / 57.3
    t_to_turn = sight_distance_m / max(speed_ms, 0.1)
    return lat_acc / max(t_to_turn, 0.1)


def brake_distance(v_ms: float, decel: float = 7.0) -> float:
    """Minimum braking distance at speed v with deceleration decel."""
    return v_ms ** 2 / (2 * decel)


def speed_advisory(segment: dict, current_speed_ms: float) -> dict:
    """Compute a safe speed for an upcoming segment.

    If braking distance at current speed exceeds sight distance,
    recommend slowing down BEFORE the hazard, not at it.
    """
    sight = segment.get("sight_distance_m", 100)
    curv = segment.get("curvature_deg_per_m", 0.0)
    # target speed: brake distance must fit within sight distance
    # v^2 / (2*7) <= sight  ->  v <= sqrt(2*7*sight)
    max_safe = math.sqrt(2 * 7.0 * sight)
    # also cap by curvature: lateral acc <= 0.3g (~2.94 m/s^2)
    if curv > 0:
        max_curv = math.sqrt(2.94 * 57.3 / math.radians(curv))
        max_safe = min(max_safe, max_curv)
    recommended = min(max_safe, segment.get("speed_limit_kmh", 60) / 3.6)
    return {
        "segment": segment["type"],
        "distance_ahead_m": segment.get("distance_ahead_m", 0),
        "current_speed_kmh": round(current_speed_ms * 3.6, 1),
        "recommended_speed_kmh": round(recommended * 3.6, 1),
        "brake_distance_m": round(brake_distance(current_speed_ms), 1),
        "sight_distance_m": sight,
        "action": "slow down" if current_speed_ms > recommended else "maintain",
    }


if __name__ == "__main__":
    mc = MapContext()
    mc.advance(150)  # approaching the right turn
    for seg in mc.upcoming(200):
        print(seg["type"], f"{seg['distance_ahead_m']:.0f}m ahead,",
              f"sight {seg.get('sight_distance_m', 'n/a')}m")
        if seg["type"] in ("right_turn", "alleyway"):
            adv = speed_advisory(seg, 40 / 3.6)
            print("  ", adv)