"""Tests for the near-field ultrasonic sonar layer."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ultrasonic_sonar import (
    UltrasonicTransducer, UltrasonicEcho, UltrasonicSonar, UltrasonicState,
    UltrasonicDetection, distance_from_echo, closing_speed_from_doppler,
    classify_object, ultrasonic_speed_factor,
    integrated_speed_advisory_with_sonar, SPEED_OF_SOUND, WAVELENGTH_M,
)
from integrated_pipeline import WifiShadowState, ShadowDetection


def test_wavelength():
    assert abs(WAVELENGTH_M - 0.008575) < 0.0001


def test_distance_from_echo_round_trip():
    # 343 m/s, 0.01 s round trip = 1.715 m
    d = distance_from_echo(0.01)
    assert abs(d - 1.715) < 0.01


def test_distance_zero_time_is_infinite():
    assert distance_from_echo(0.0) == float('inf')


def test_doppler_closing_speed():
    # 400 Hz shift at 40 kHz -> v = 400*343/(2*40000) = 1.715 m/s
    v = closing_speed_from_doppler(400.0)
    assert abs(v - 1.715) < 0.01


def test_classify_curb():
    assert classify_object(1.0, 0.2, 0.0) == 'curb'


def test_classify_vehicle():
    assert classify_object(5.0, 0.8, 0.0, width_estimate_m=2.0) == 'vehicle'


def test_classify_pedestrian():
    assert classify_object(2.0, 0.5, 600.0) == 'pedestrian'


def test_dead_zone_rejected():
    sonar = UltrasonicSonar()
    echoes = [UltrasonicEcho(0, 0.001, 0.9, 0.0)]  # 0.17 m - inside dead zone
    state = sonar.process_echoes(echoes)
    assert len(state.detections) == 0


def test_max_range_rejected():
    sonar = UltrasonicSonar()
    echoes = [UltrasonicEcho(0, 0.07, 0.9, 0.0)]  # ~12 m - out of range
    state = sonar.process_echoes(echoes)
    assert len(state.detections) == 0


def test_valid_detection():
    sonar = UltrasonicSonar()
    echoes = [UltrasonicEcho(1, 0.02, 0.8, 200.0)]  # ~3.4 m, closing
    state = sonar.process_echoes(echoes, timestamp_ms=1000)
    assert len(state.detections) == 1
    d = state.detections[0]
    assert abs(d.distance_m - 3.43) < 0.05
    assert d.bearing_deg == -15.0
    assert d.confidence > 0.3
    assert d.object_type == 'pedestrian'


def test_emergency_advisory_under_one_meter():
    sonar = UltrasonicSonar()
    echoes = [UltrasonicEcho(2, 0.004, 0.9, 0.0)]  # ~0.69 m
    state = sonar.process_echoes(echoes)
    assert state.advisory is not None
    assert 'NEAR-FIELD' in state.advisory
    assert state.min_distance_m < 1.0


def test_speed_factor_emergency():
    st = UltrasonicState(min_distance_m=0.5)
    assert ultrasonic_speed_factor(st) == 0.1


def test_speed_factor_mid_range():
    st = UltrasonicState(min_distance_m=2.0)
    assert ultrasonic_speed_factor(st) == 0.5


def test_speed_factor_far():
    st = UltrasonicState(min_distance_m=6.0)
    assert ultrasonic_speed_factor(st) == 1.0


def test_integrated_with_sonar_stacks():
    # Wet + sharp + shadow + near-field sonar = very low advisory
    shadow = WifiShadowState(
        [ShadowDetection(0, 25, 0.7, 'wifi', 0.5, 0)], 5, 3, -60.0, 0.5)
    sonar = UltrasonicState(
        [UltrasonicDetection(0.8, -15.0, 0.9, 'curb', 0.0, 0)], 0.8, -15.0)
    adv = integrated_speed_advisory_with_sonar(
        60, 0.4, 0.8, 0.5, 30, shadow, sonar)
    assert adv == 5.0  # floor


def test_sonar_alone_reduces_speed():
    shadow = WifiShadowState([], 5, 3, -60.0, 0.0)
    sonar = UltrasonicState(
        [UltrasonicDetection(2.5, 15.0, 0.8, 'debris', 1.0, 0)], 2.5, 15.0)
    adv = integrated_speed_advisory_with_sonar(
        60, 0.9, 0.1, 0.1, 100, shadow, sonar)
    # base ~59 * 0.5 (sonar 1-3m) ≈ 29.5
    assert 25 <= adv <= 35


if __name__ == '__main__':
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f'PASS {t.__name__}')
        except Exception as e:
            print(f'FAIL {t.__name__}: {e}')
    print(f'{passed}/{len(tests)} passed')
    sys.exit(0 if passed == len(tests) else 1)
