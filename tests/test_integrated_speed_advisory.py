"""Tests for the integrated speed advisory combining map, traction, and RF shadow."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from integrated_pipeline import (
    ShadowDetection, WifiShadowState, integrated_speed_advisory, PipelineFrame,
)


def _shadow_state(density, n_dets):
    dets = [ShadowDetection(0, 25, 0.7, 'wifi', 0.5, 0) for _ in range(n_dets)]
    return WifiShadowState(dets, 5, 3, -60.0, density)


def test_dry_clear_no_shadow():
    adv = integrated_speed_advisory(60, 0.9, 0.1, 0.1, 100, _shadow_state(0.0, 0))
    assert 55 <= adv <= 65, f"got {adv}"


def test_wet_low_grip():
    adv = integrated_speed_advisory(60, 0.4, 0.8, 0.1, 100, _shadow_state(0.0, 0))
    assert 28 <= adv <= 36, f"got {adv}"


def test_sharp_turn_short_sight():
    adv = integrated_speed_advisory(60, 0.9, 0.1, 0.5, 30, _shadow_state(0.0, 0))
    assert 20 <= adv <= 30, f"got {adv}"


def test_wet_sharp_with_shadow():
    adv = integrated_speed_advisory(60, 0.4, 0.8, 0.5, 30, _shadow_state(0.5, 2))
    assert 8 <= adv <= 16, f"got {adv}"


def test_fog_shadow_only():
    adv = integrated_speed_advisory(60, 0.9, 0.1, 0.1, 100, _shadow_state(0.4, 3))
    assert 28 <= adv <= 38, f"got {adv}"


def test_floor_at_five_kmh():
    # Extreme case: everything bad
    adv = integrated_speed_advisory(10, 0.2, 0.9, 0.9, 10, _shadow_state(0.6, 4))
    assert adv >= 5.0


def test_pipeline_frame_collects_advisories():
    frame = PipelineFrame(
        base_speed=60, grip=0.4, wetness=0.8, curvature=0.5, sight_m=30,
        shadow_state=_shadow_state(0.5, 2),
    )
    adv = frame.run()
    assert 8 <= adv <= 16
    assert len(frame.advisories) >= 3  # traction, wetness, geometry, shadow


def test_no_advisories_on_clean_frame():
    frame = PipelineFrame(
        base_speed=60, grip=0.9, wetness=0.1, curvature=0.1, sight_m=100,
        shadow_state=_shadow_state(0.0, 0),
    )
    frame.run()
    assert len(frame.advisories) == 0


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
