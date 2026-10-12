"""System heartbeat and vitality monitor from v1.2.0-GOLD.

Tracks compute load, heartbeat percentage, and CPU temperature.
"""


def update_heartbeat(prev: dict, rng=None) -> dict:
    """Update system health metrics (mirrors v1.2.0 tick logic)."""
    import random
    if rng is None:
        rng = random
    return {
        "compute": min(100, max(30, prev.get("compute", 42) + (rng.random() * 14 - 7))),
        "heartbeat": min(100, max(85, prev.get("heartbeat", 99) + (rng.random() * 4 - 2))),
        "cpu_temp": min(85, max(40, prev.get("cpu_temp", 45) + (rng.random() * 2 - 1))),
    }


if __name__ == "__main__":
    h = {"compute": 42, "heartbeat": 99, "cpu_temp": 45}
    for _ in range(5):
        h = update_heartbeat(h)
        print(h)