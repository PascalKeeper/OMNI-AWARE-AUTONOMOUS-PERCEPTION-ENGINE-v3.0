# Author: Joseph Rocco Peransi
"""Near-field ultrasonic echolocation layer — bat-inspired sonar.

Complement to the existing 77 GHz radar. Ultrasound gives centimeter-scale
resolution at 0.3-10 m where radar resolution is coarse and cameras are
blind at night or in fog. Bats solve this with short broadband chirps;
this module models the same pipeline: emit pulse, timestamp echo return,
convert time-of-flight to distance, use multi-transducer bearing, and
feed detections into the same advisory system as RF shadows, traction,
and map context.

Physics:
- Speed of sound in air at 20 C: ~343 m/s
- 40 kHz wavelength: ~8.6 mm — sub-centimeter resolution potential
- Round-trip: distance = (echo_time_s * 343) / 2
- Attenuation in air: ~1.5-2 dB/m at 40 kHz (humidity-dependent)
- Practical range: 0.3 m (near-field dead zone) to ~10 m
- Doppler: speed = (delta_f / f0) * 343 / 2 for closing/opening rate

Hardware assumption: 8-transducer ring array (4 front, 2 left, 2 right),
40 kHz center frequency, 2 ms chirp, 50 Hz ping rate. Matches commercial
parking-sensor arrays (e.g., Valeo, Bosch) but with software fusion into
the OMNI-AWARE decision layer rather than standalone alerts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict

SPEED_OF_SOUND = 343.0  # m/s at 20 C
ULTRASONIC_FREQ_HZ = 40000.0
WAVELENGTH_M = SPEED_OF_SOUND / ULTRASONIC_FREQ_HZ  # ~8.6 mm
NEAR_FIELD_DEAD_ZONE_M = 0.3
MAX_RANGE_M = 10.0
PING_RATE_HZ = 50.0


@dataclass
class UltrasonicTransducer:
    """One transducer in the ring array."""
    id: int
    bearing_deg: float  # 0 = forward, negative = left, positive = right
    position_m: tuple  # (x forward, y lateral) relative to vehicle center


@dataclass
class UltrasonicEcho:
    """One echo return from one transducer."""
    transducer_id: int
    echo_time_s: float  # round-trip time
    amplitude: float  # 0-1 normalized
    doppler_shift_hz: float  # positive = closing


@dataclass
class UltrasonicDetection:
    """A near-field object detected by the sonar layer."""
    distance_m: float
    bearing_deg: float
    confidence: float
    object_type: str  # 'curb', 'pedestrian', 'vehicle', 'debris', 'unknown'
    closing_speed_mps: float
    timestamp_ms: int


@dataclass
class UltrasonicState:
    """Aggregated sonar state for one pipeline frame."""
    detections: List[UltrasonicDetection] = field(default_factory=list)
    min_distance_m: float = float('inf')
    nearest_bearing_deg: float = 0.0
    advisory: Optional[str] = None


def distance_from_echo(echo_time_s: float) -> float:
    """Round-trip time of flight to distance."""
    if echo_time_s <= 0:
        return float('inf')
    return (echo_time_s * SPEED_OF_SOUND) / 2.0


def closing_speed_from_doppler(doppler_shift_hz: float) -> float:
    """Doppler shift to closing speed. v = df * c / (2 * f0)."""
    return doppler_shift_hz * SPEED_OF_SOUND / (2 * ULTRASONIC_FREQ_HZ)


def classify_object(distance_m: float, amplitude: float,
                    doppler_shift_hz: float, width_estimate_m: float = 0.0) -> str:
    """Heuristic classification from echo signature.

    Low amplitude + close = curb or low debris.
    High amplitude + wide = vehicle.
    Medium + moving (doppler) = pedestrian.
    """
    speed = abs(closing_speed_from_doppler(doppler_shift_hz))
    if amplitude < 0.3 and distance_m < 2.0:
        return 'curb'
    if amplitude > 0.7 and width_estimate_m > 1.5:
        return 'vehicle'
    if speed > 0.5 and 0.5 < distance_m < 5.0:
        return 'pedestrian'
    if amplitude > 0.5:
        return 'debris'
    return 'unknown'


class UltrasonicSonar:
    """Near-field echolocation array.

    8 transducers in a ring. Each ping cycle: emit 2 ms chirp at 40 kHz,
    listen for returns, timestamp, classify, fuse bearings.
    """

    def __init__(self, transducers: Optional[List[UltrasonicTransducer]] = None):
        if transducers is None:
            # Default 8-transducer ring: 4 front, 2 left, 2 right
            self.transducers = [
                UltrasonicTransducer(0, -45.0, (-0.1, -0.4)),
                UltrasonicTransducer(1, -15.0, (-0.1, -0.15)),
                UltrasonicTransducer(2, 15.0, (-0.1, 0.15)),
                UltrasonicTransducer(3, 45.0, (-0.1, 0.4)),
                UltrasonicTransducer(4, -30.0, (-0.5, -0.3)),
                UltrasonicTransducer(5, 30.0, (-0.5, 0.3)),
                UltrasonicTransducer(6, -60.0, (-0.3, -0.5)),
                UltrasonicTransducer(7, 60.0, (-0.3, 0.5)),
            ]
        else:
            self.transducers = transducers
        self._tx_by_id = {t.id: t for t in self.transducers}

    def process_echoes(self, echoes: List[UltrasonicEcho],
                       timestamp_ms: int = 0) -> UltrasonicState:
        """Convert raw echo returns into classified near-field detections."""
        detections: List[UltrasonicDetection] = []
        for echo in echoes:
            tx = self._tx_by_id.get(echo.transducer_id)
            if tx is None:
                continue
            dist = distance_from_echo(echo.echo_time_s)
            if dist < NEAR_FIELD_DEAD_ZONE_M or dist > MAX_RANGE_M:
                continue  # dead zone or out of range
            # Confidence: stronger echo + closer = more confident
            conf = min(0.95, echo.amplitude * (1.0 - dist / MAX_RANGE_M) * 1.2)
            if conf < 0.3:
                continue
            speed = closing_speed_from_doppler(echo.doppler_shift_hz)
            obj_type = classify_object(dist, echo.amplitude, echo.doppler_shift_hz)
            detections.append(UltrasonicDetection(
                distance_m=dist,
                bearing_deg=tx.bearing_deg,
                confidence=conf,
                object_type=obj_type,
                closing_speed_mps=speed,
                timestamp_ms=timestamp_ms,
            ))

        min_dist = min((d.distance_m for d in detections), default=float('inf'))
        nearest_bearing = 0.0
        if detections:
            nearest = min(detections, key=lambda d: d.distance_m)
            nearest_bearing = nearest.bearing_deg

        advisory = None
        if min_dist < 1.0:
            types = sorted({d.object_type for d in detections if d.distance_m < 1.0})
            advisory = (f"NEAR-FIELD OBSTRUCTION at {min_dist:.1f}m "
                        f"({', '.join(types)}) bearing {nearest_bearing:+.0f} deg. "
                        f"Brake or steer.")
        elif min_dist < 3.0:
            advisory = (f"Near-field object at {min_dist:.1f}m bearing "
                        f"{nearest_bearing:+.0f} deg. Slow approach.")

        return UltrasonicState(
            detections=detections,
            min_distance_m=min_dist,
            nearest_bearing_deg=nearest_bearing,
            advisory=advisory,
        )


# --- Integration with the speed advisory ---

def ultrasonic_speed_factor(state: UltrasonicState) -> float:
    """Speed multiplier from near-field sonar.

    Under 1 m: emergency floor (0.1). 1-3 m: 0.5. 3-5 m: 0.75. Beyond: 1.0.
    """
    if state.min_distance_m < 1.0:
        return 0.1
    if state.min_distance_m < 3.0:
        return 0.5
    if state.min_distance_m < 5.0:
        return 0.75
    return 1.0


def integrated_speed_advisory_with_sonar(
    base_speed: float,
    grip: float,
    wetness: float,
    curvature: float,
    sight_m: float,
    shadow_state: WifiShadowState,
    sonar_state: UltrasonicState,
) -> float:
    """Full advisory: map + traction + RF shadow + ultrasonic near-field."""
    from integrated_pipeline import integrated_speed_advisory
    speed = integrated_speed_advisory(
        base_speed, grip, wetness, curvature, sight_m, shadow_state,
    )
    speed *= ultrasonic_speed_factor(sonar_state)
    return max(speed, 5.0)
