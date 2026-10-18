"""Tests for shared feature buffer."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from shared_feature_buffer import SharedFeatureBuffer, stopping_distance_saved_m

def test_process_once_and_read():
    buf = SharedFeatureBuffer()
    frame = {"rgb_mean": [0.2, 0.5, 0.1], "quadrant_activity": [0.1, 0.2, 0.3, 0.4]}
    handle = buf.process_once(frame, timestamp_ms=1000)
    assert buf.read(handle, "rgb_mean") == [0.2, 0.5, 0.1]
    assert buf.read(handle, "quadrant_activity")[2] == 0.3

def test_stale_handle_raises():
    buf = SharedFeatureBuffer()
    h1 = buf.process_once({}, 1000)
    buf.process_once({}, 2000)  # new buffer_id
    try:
        buf.read(h1, "rgb_mean")
        assert False, "should have raised"
    except RuntimeError:
        pass

def test_head_isolation():
    buf = SharedFeatureBuffer()
    buf.register_head("ransac")
    buf.register_head("fusion")
    buf.head_failed("ransac")
    assert "fusion" in buf.alive_heads()
    assert "ransac" not in buf.alive_heads()

def test_stopping_distance_claim():
    # Podcast: 95% latency cut at 40 mph → ~4.14 m
    saved = stopping_distance_saved_m(40.0, 95.0)
    assert 3.5 < saved < 4.5

def test_memory_overhead_small_in_python():
    buf = SharedFeatureBuffer()
    assert buf.memory_overhead_mb() < 1.0

if __name__ == "__main__":
    for t in [v for k,v in globals().items() if k.startswith("test_")]:
        t()
        print("PASS", t.__name__)
    print("all passed")
