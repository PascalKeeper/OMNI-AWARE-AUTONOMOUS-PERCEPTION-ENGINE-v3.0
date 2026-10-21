# Author: Joseph Rocco Peransi
"""AI Co-Pilot: Grok API mandate with Gemini backdoor.

Primary: xAI Grok API (XAI_API_KEY).
Backdoor: Google Gemini API (GEMINI_API_KEY) for cross-platform
compatibility if a Tesla-xAI deal ever materializes.
The mandate is Grok-first; Gemini is fallback only.
"""
import json
import os
import urllib.request
import urllib.error

GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-4"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash-preview-09-2025:generateContent"
)

SCENE_PROMPT = """You are the AI Co-Pilot of an autonomous vehicle.
Analyze this telemetry snapshot: {context}

Output a SINGLE concise sentence (max 20 words) assessing the risk level
and recommending a driving action. Style: Robotic, urgent, professional.
Example: "CRITICAL: Pedestrian detected in center lane. Initiating emergency braking protocol."
"""

REPORT_PROMPT = """You are the Fleet Management AI.
Summarize these vehicle system logs into a brief Incident Report for the
Project Director: {context}

Focus on critical warnings and system health. Use bullet points.
"""


def _call_grok(prompt: str, api_key: str) -> str:
    payload = {
        "model": GROK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 100,
    }
    req = urllib.request.Request(
        GROK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"].strip()


def _call_gemini(prompt: str, api_key: str) -> str:
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    req = urllib.request.Request(
        f"{GEMINI_URL}?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["candidates"][0]["content"]["parts"][0]["text"].strip()


def analyze_scene(context: dict, grok_key: str = None, gemini_key: str = None) -> dict:
    """Grok-first scene analysis with Gemini backdoor.

    Returns {text, provider}. Raises if both providers fail.
    """
    if grok_key is None:
        grok_key = os.environ.get("XAI_API_KEY")
    if gemini_key is None:
        gemini_key = os.environ.get("GEMINI_API_KEY")

    prompt = SCENE_PROMPT.format(context=json.dumps(context))

    # Mandate: Grok first
    if grok_key:
        try:
            return {"text": _call_grok(prompt, grok_key), "provider": "grok"}
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError):
            pass  # fall through to backdoor

    # Backdoor: Gemini (cross-platform compatibility)
    if gemini_key:
        try:
            return {"text": _call_gemini(prompt, gemini_key), "provider": "gemini"}
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError):
            pass

    return {"text": "Neural Connection Offline.", "provider": "none"}


def generate_report(logs: list, grok_key: str = None, gemini_key: str = None) -> dict:
    """Grok-first incident report with Gemini backdoor."""
    if grok_key is None:
        grok_key = os.environ.get("XAI_API_KEY")
    if gemini_key is None:
        gemini_key = os.environ.get("GEMINI_API_KEY")

    prompt = REPORT_PROMPT.format(context=json.dumps(logs[:10]))

    if grok_key:
        try:
            return {"text": _call_grok(prompt, grok_key), "provider": "grok"}
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError):
            pass

    if gemini_key:
        try:
            return {"text": _call_gemini(prompt, gemini_key), "provider": "gemini"}
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError):
            pass

    return {"text": "Insufficient data for report generation.", "provider": "none"}


if __name__ == "__main__":
    ctx = {"speed": "72 km/h", "detected_objects": [{"type": "PEDESTRIAN", "distance": "15.0m", "lane": "Center"}]}
    print(analyze_scene(ctx))  # no keys -> offline fallback