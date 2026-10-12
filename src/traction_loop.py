"""Traction loop: wheels, visual surface, and sound talking to each other.

The system cross-references three independent signals:
1. Wheel slip (tires) - are we actually gripping?
2. Visual surface (camera) - does the asphalt look wet/gravelly?
3. Acoustic signature (microphones) - what does the road sound like?

When they agree, confidence is high. When they disagree, that's the
interesting case - the system flags it and adjusts.
"""
import math


# ---------- 1. Wheel slip sensor ----------
def traction_from_tires(slip_ratio: float) -> dict:
    """Estimate grip from wheel slip.

    slip_ratio = (wheel_speed - vehicle_speed) / vehicle_speed.
    Positive slip = wheel spinning faster than road (acceleration).
    Negative slip = wheel locked (braking).
    """
    grip = max(0.0, 1.0 - abs(slip_ratio) * 5)
    return {
        "slip_ratio": round(slip_ratio, 3),
        "grip": round(grip, 2),
        "traction_ok": grip > 0.6,
    }


# ---------- 2. Visual surface classifier ----------
def surface_from_visual(glimmer: float, gravelly: float) -> dict:
    """Estimate surface wetness from visual cues.

    glimmer = specular reflection intensity (wet asphalt glistens).
    gravelly = texture roughness score.
    """
    wetness = min(1.0, glimmer * 1.5 + gravelly * 0.3)
    return {
        "wetness": round(wetness, 2),
        "surface": "wet" if wetness > 0.5 else "dry",
        "gravelly": gravelly > 0.5,
    }


# ---------- 3. Acoustic surface classifier ----------
def classify_sound(spectrum: dict) -> str:
    """Classify surface from tire noise spectrum.

    gravel: high-frequency broadband hiss (2-8 kHz)
    water: low-frequency rumble + splash (50-200 Hz)
    dry asphalt: mid-frequency hum (200-2000 Hz)
    """
    hf = spectrum.get("high_freq", 0)
    lf = spectrum.get("low_freq", 0)
    mf = spectrum.get("mid_freq", 0)
    if hf > lf and hf > mf:
        return "gravel"
    if lf > hf and lf > mf:
        return "water"
    return "dry_asphalt"


# ---------- 4. The cross-reference loop ----------
def cross_reference(visual: dict, tires: dict, sound: str = None) -> dict:
    """Compare visual surface estimate against actual tire grip.

    This is the 'talking to itself' step: the system notices when
    what it sees doesn't match what the tires feel.
    """
    wet = visual["wetness"]
    grip = tires["grip"]

    # Sound can break ties or raise confidence
    sound_agrees_wet = sound == "water"
    sound_agrees_dry = sound == "dry_asphalt"
    sound_agrees_gravel = sound == "gravel"

    if wet > 0.5 and grip > 0.6:
        conf = "high" if sound_agrees_wet else "medium"
        return {"conclusion": "surface looks wet but tires are holding",
                "confidence": conf, "action": "maintain speed, monitor"}
    if wet > 0.5 and grip < 0.6:
        conf = "high" if sound_agrees_wet else "medium"
        return {"conclusion": "wet surface AND losing traction",
                "confidence": conf, "action": "reduce speed, increase following distance"}
    if wet < 0.3 and grip < 0.6:
        conf = "high" if sound_agrees_dry else "medium"
        return {"conclusion": "surface looks dry but tires slipping",
                "confidence": conf, "action": "check tire pressure/tread"}
    if visual.get("gravelly") and sound_agrees_gravel:
        return {"conclusion": "gravel surface confirmed by sight and sound",
                "confidence": "high", "action": "reduce speed, expect reduced grip"}
    return {"conclusion": "surface and tires agree", "confidence": "medium", "action": "normal operation"}


if __name__ == "__main__":
    # Scenario: wet asphalt, tires holding
    vis = surface_from_visual(0.8, 0.2)
    tires = traction_from_tires(0.02)
    print(vis, tires, cross_reference(vis, tires, "water"))

    # Scenario: wet asphalt, losing grip
    tires2 = traction_from_tires(0.25)
    print(vis, tires2, cross_reference(vis, tires2, "water"))

    # Scenario: gravelly road
    vis3 = surface_from_visual(0.1, 0.7)
    tires3 = traction_from_tires(0.05)
    print(vis3, tires3, cross_reference(vis3, tires3, "gravel"))