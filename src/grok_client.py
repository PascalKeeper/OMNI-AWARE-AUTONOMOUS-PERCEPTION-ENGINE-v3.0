"""Grok API integration for cloud hazard analysis.

Sends outlier frames and hazard metadata to Grok for semantic
classification. Falls back to local heuristics when the API is
unavailable, rate-limited, or the network is down.
"""
import base64
import json
import os
import time
import urllib.request
import urllib.error

import numpy as np

GROK_API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-4"

HAZARD_PROMPT = """You are a perception engine analyzing a road hazard frame.
The frame is a grayscale image where outliers (non-road pixels) have been
flagged by RANSAC. Classify the hazard and estimate its threat level.

Respond with ONLY valid JSON, no markdown:
{
  "hazard_type": "boulder" | "log" | "debris" | "cliff" | "waterfall" | "unknown",
  "threat_level": "low" | "medium" | "high" | "critical",
  "estimated_size_m": <number>,
  "recommended_action": "<one sentence>",
  "confidence": <0.0-1.0>
}
"""


def _encode_frame(gray: np.ndarray) -> str:
    """Downsample and base64-encode a grayscale frame for the API."""
    small = gray[::4, ::4]  # 4x downsample to keep payload small
    small = (small / small.max() * 255).astype(np.uint8) if small.max() > 0 else small.astype(np.uint8)
    return base64.b64encode(small.tobytes()).decode("ascii")


def analyze_hazard(gray: np.ndarray, outlier_points: list, api_key: str = None) -> dict:
    """Send outlier frame to Grok for semantic hazard analysis.

    Returns a dict with hazard_type, threat_level, etc.
    Falls back to local classification on any failure.
    """
    if api_key is None:
        api_key = os.environ.get("XAI_API_KEY")

    if not api_key:
        return _local_fallback(outlier_points)

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": HAZARD_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "frame_shape": list(gray.shape),
                        "n_outliers": len(outlier_points),
                        "outlier_sample": outlier_points[:10],
                        "frame_b64": _encode_frame(gray),
                    }
                ),
            },
        ],
        "temperature": 0.0,
        "max_tokens": 200,
    }

    req = urllib.request.Request(
        GROK_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        text = body["choices"][0]["message"]["content"].strip()
        # strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError, TimeoutError) as e:
        return _local_fallback(outlier_points, error=str(e))


def _local_fallback(outlier_points: list, error: str = None) -> dict:
    """Local heuristic classification when the API is unreachable."""
    n = len(outlier_points)
    if n == 0:
        return {
            "hazard_type": "none",
            "threat_level": "low",
            "estimated_size_m": 0.0,
            "recommended_action": "No hazard detected.",
            "confidence": 1.0,
            "source": "local_fallback",
        }
    # cluster outliers to estimate size
    pts = np.array(outlier_points)
    spread = float(np.ptp(pts, axis=0).max()) if len(pts) > 1 else 0.0
    size_m = spread / 100.0  # rough: 100 px ~ 1 m at typical range
    if size_m > 2.0:
        htype, threat = "boulder", "high"
    elif size_m > 0.5:
        htype, threat = "log", "medium"
    else:
        htype, threat = "debris", "low"
    return {
        "hazard_type": htype,
        "threat_level": threat,
        "estimated_size_m": round(size_m, 2),
        "recommended_action": f"Avoid {htype}; estimated size {size_m:.1f} m.",
        "confidence": 0.6,
        "source": "local_fallback",
        "error": error,
    }


if __name__ == "__main__":
    # demo with synthetic outliers
    rng = np.random.default_rng(0)
    gray = rng.random((1080, 1920)) * 40 + 80
    gray[500:560, 900:980] = 200  # bright boulder patch
    outliers = [[x, y] for y in range(500, 560) for x in range(900, 980)]
    result = analyze_hazard(gray, outliers)
    print(json.dumps(result, indent=2))