"""WebSocket telemetry server for the Tesla HUD.

Streams pipeline results (hazards, decisions, evasion) to the
Tesla browser HUD in real time. Run alongside pipeline.py.
"""
import asyncio
import json
import sys
sys.path.insert(0, "../src")

try:
    import websockets
except ImportError:
    print("pip install websockets")
    sys.exit(1)

from pipeline import PerceptionEngine
import numpy as np

HOST = "0.0.0.0"
PORT = 8765


async def handler(ws):
    """Send telemetry to connected HUD clients."""
    engine = PerceptionEngine()
    rng = np.random.default_rng()
    while True:
        img = rng.random((1080, 1920, 3)).astype(np.float32) * 60 + 60
        if rng.random() > 0.85:
            img[500:560, 900:980] = 220  # inject hazard
        result = engine.process_frame(img)
        # slim payload for the HUD
        payload = {
            "hazards": [
                {"type": r["hazard_type"], "threat": r["threat_level"],
                 "x": 960, "y": 540, "size": 30}
                for r in result["grok_results"] if r["hazard_type"] != "none"
            ],
            "decision": result["decision"],
            "evasion": result["physics"]["evasion"] if result["physics"] else None,
            "fps": round(1000 / max(result["elapsed_ms"], 0.1), 0),
        }
        try:
            await ws.send(json.dumps(payload))
        except websockets.ConnectionClosed:
            break
        await asyncio.sleep(0.05)  # ~20 Hz to the HUD


async def main():
    async with websockets.serve(handler, HOST, PORT):
        print(f"Telemetry server on ws://{HOST}:{PORT}")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())