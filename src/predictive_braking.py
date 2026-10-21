# Author: Joseph Rocco Peransi
"""Predictive braking: collision warning before impact.

Ported from OmniAwareDashboard v1.0.4 (Nov 2025).
Flags any entity within 20 meters in the ego lane (abs(x) < 20).
"""

BRAKE_THRESHOLD_M = 20.0
LANE_WIDTH = 20.0  # abs(x) < 20 = in ego lane


def check_collision_warning(entities: list) -> list:
    """Return entities triggering a collision warning."""
    warnings = []
    for e in entities:
        if e["z"] < BRAKE_THRESHOLD_M and abs(e["x"]) < LANE_WIDTH:
            warnings.append(e)
    return warnings


def should_brake(entities: list) -> bool:
    """True if any entity is in braking range in the ego lane."""
    return len(check_collision_warning(entities)) > 0


if __name__ == "__main__":
    ents = [{"type": "PEDESTRIAN", "x": 0, "z": 15}, {"type": "CAR", "x": 50, "z": 10}]
    w = check_collision_warning(ents)
    print(f"Warnings: {len(w)} -> {should_brake(ents)}")