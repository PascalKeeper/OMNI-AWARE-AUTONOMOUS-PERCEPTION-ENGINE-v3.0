"""Tests for the traction loop: visual, tires, sound."""
import sys
sys.path.insert(0, "../src")

from traction_loop import surface_from_visual, traction_from_tires, classify_sound, cross_reference


def test_wet_surface_high_glimmer():
    v = surface_from_visual(0.8, 0.1)
    assert v["wetness"] > 0.5
    assert v["surface"] == "wet"


def test_dry_surface_low_glimmer():
    v = surface_from_visual(0.1, 0.1)
    assert v["wetness"] < 0.5
    assert v["surface"] == "dry"


def test_gravelly_flag():
    v = surface_from_visual(0.1, 0.7)
    assert v["gravelly"] is True


def test_traction_ok_low_slip():
    t = traction_from_tires(0.02)
    assert t["traction_ok"] is True
    assert t["grip"] > 0.6


def test_traction_fail_high_slip():
    t = traction_from_tires(0.25)
    assert t["traction_ok"] is False
    assert t["grip"] < 0.6


def test_sound_gravel():
    assert classify_sound({"high_freq": 0.8, "low_freq": 0.2, "mid_freq": 0.3}) == "gravel"


def test_sound_water():
    assert classify_sound({"high_freq": 0.2, "low_freq": 0.8, "mid_freq": 0.3}) == "water"


def test_sound_dry():
    assert classify_sound({"high_freq": 0.3, "low_freq": 0.2, "mid_freq": 0.8}) == "dry_asphalt"


def test_cross_ref_wet_gripping():
    v = surface_from_visual(0.8, 0.2)
    t = traction_from_tires(0.02)
    r = cross_reference(v, t, "water")
    assert "holding" in r["conclusion"]
    assert r["action"] == "maintain speed, monitor"


def test_cross_ref_wet_slipping():
    v = surface_from_visual(0.8, 0.2)
    t = traction_from_tires(0.25)
    r = cross_reference(v, t, "water")
    assert "losing traction" in r["conclusion"]
    assert "reduce speed" in r["action"]


def test_cross_ref_dry_slipping():
    v = surface_from_visual(0.1, 0.1)
    t = traction_from_tires(0.15)
    r = cross_reference(v, t, "dry_asphalt")
    assert "dry" in r["conclusion"] and "slipping" in r["conclusion"]


def test_cross_ref_gravel():
    v = surface_from_visual(0.1, 0.7)
    t = traction_from_tires(0.05)
    r = cross_reference(v, t, "gravel")
    assert "gravel" in r["conclusion"]


if __name__ == "__main__":
    test_wet_surface_high_glimmer()
    test_dry_surface_low_glimmer()
    test_gravelly_flag()
    test_traction_ok_low_slip()
    test_traction_fail_high_slip()
    test_sound_gravel()
    test_sound_water()
    test_sound_dry()
    test_cross_ref_wet_gripping()
    test_cross_ref_wet_slipping()
    test_cross_ref_dry_slipping()
    test_cross_ref_gravel()
    print("All traction loop tests passed.")