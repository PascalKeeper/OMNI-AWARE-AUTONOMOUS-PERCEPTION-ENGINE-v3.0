"""Temporal persistence: 3 consecutive hits to promote, 3 misses or 10 frames to drop."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from temporal_filter import TemporalFilter


def test_flicker_never_promotes():
    jumping = TemporalFilter()
    for i in range(5):
        confirmed = jumping.update([(i * 5.0, 0.0)], frame=i, hazard_type="shadow")
        assert confirmed == []
    flicker = TemporalFilter()
    for i in range(5):
        points = [(0.0, 5.0)] if i % 2 == 0 else []
        confirmed = flicker.update(points, frame=i, hazard_type="shadow")
        assert confirmed == []


def test_boulder_promotes_on_frame_3():
    filt = TemporalFilter()
    confirmed = []
    for i in range(4):
        confirmed = filt.update([(1.0, 8.0)], frame=i, hazard_type="boulder")
        if i < 2:
            assert confirmed == []
        if i == 2:
            assert len(confirmed) == 1
            assert confirmed[0].hit_count == 3
            assert confirmed[0].hazard_type == "boulder"
    assert len(confirmed) == 1
    assert confirmed[0].hit_count == 4


def test_track_dropped_after_4_misses():
    filt = TemporalFilter()
    filt.update([(0.0, 10.0)], frame=0, hazard_type="boulder")
    for i in range(1, 5):
        filt.update([], frame=i, hazard_type="boulder")
    assert filt.tracks == []


def test_fast_car_expires_by_max_age():
    filt = TemporalFilter(max_age=10)
    filt.update([(0.0, 20.0)], frame=0, hazard_type="car")
    filt.update([(1.0, 20.0)], frame=1, hazard_type="car")
    assert len(filt.tracks) == 1
    assert filt.tracks[0].hit_count == 2
    filt.update([], frame=4)
    assert len(filt.tracks) == 1
    assert filt.tracks[0].miss_count < 4
    filt.update([], frame=11)
    assert filt.tracks == []


if __name__ == "__main__":
    test_flicker_never_promotes()
    test_boulder_promotes_on_frame_3()
    test_track_dropped_after_4_misses()
    test_fast_car_expires_by_max_age()
    print("temporal filter tests passed")
