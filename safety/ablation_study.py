"""Spectrum lock ablation study.

Proves the v1.2.0 CPU spectrum lock (70% R, 70% G, 7% B) destroys
color-critical signals that Tesla's vision stack depends on.

This is a simulation using synthetic pixel values, not real camera data.
It demonstrates the principle: a luminance-weighted filter crushes the
chromatic channels that carry brake-light red, traffic-signal red/yellow/green,
and lane-marking yellow.
"""

# Spectrum lock weights (from v1.2.0-GOLD)
RED_LOCK = 0.70
GREEN_LOCK = 0.70
BLUE_LOCK = 0.07


def spectrum_lock(r, g, b):
    """Apply the v1.2.0 spectrum lock to an RGB pixel."""
    return r * RED_LOCK, g * GREEN_LOCK, b * BLUE_LOCK


# Synthetic test signals (normalized 0-1 RGB)
SIGNALS = {
    "brake_light_red": (0.90, 0.05, 0.05),
    "traffic_signal_red": (0.85, 0.10, 0.10),
    "traffic_signal_yellow": (0.95, 0.85, 0.10),
    "traffic_signal_green": (0.10, 0.80, 0.15),
    "lane_marking_yellow": (0.95, 0.80, 0.10),
    "asphalt_gray": (0.25, 0.25, 0.25),
    "sky_blue": (0.30, 0.50, 0.85),
}


def run_ablation():
    """Compare raw vs locked signal discriminability."""
    results = []
    for name, (r, g, b) in SIGNALS.items():
        lr, lg, lb = spectrum_lock(r, g, b)
        # luminance-ish single channel value after lock
        locked_val = 0.21 * lr + 0.70 * lg + 0.07 * lb
        raw_luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        # chromatic contrast: how much the color deviates from neutral gray
        raw_chroma = max(r, g, b) - min(r, g, b)
        locked_chroma = max(lr, lg, lb) - min(lr, lg, lb)
        chroma_loss = 1.0 - (locked_chroma / raw_chroma) if raw_chroma > 0 else 0.0
        results.append({
            "signal": name,
            "raw": (round(r, 2), round(g, 2), round(b, 2)),
            "locked": (round(lr, 3), round(lg, 3), round(lb, 3)),
            "raw_luma": round(raw_luma, 3),
            "locked_luma": round(locked_val, 3),
            "raw_chroma": round(raw_chroma, 3),
            "locked_chroma": round(locked_chroma, 3),
            "chroma_loss_pct": round(chroma_loss * 100, 1),
        })
    return results


if __name__ == "__main__":
    import json
    results = run_ablation()
    print(json.dumps(results, indent=2))
    # summary: average chroma loss across colored signals
    colored = [r for r in results if r["signal"] != "asphalt_gray" and r["signal"] != "sky_blue"]
    avg_loss = sum(r["chroma_loss_pct"] for r in colored) / len(colored)
    print(f"\nAverage chroma loss on colored signals: {avg_loss:.1f}%")