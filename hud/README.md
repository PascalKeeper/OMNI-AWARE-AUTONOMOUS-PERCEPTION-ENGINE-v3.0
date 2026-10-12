# Tesla HUD — OMNI-AWARE v3.0

## Components

- **tesla_hud.py** — SVG renderer for hazard markers, evasion arrows, decision banners. Works on Tesla's 17-inch center display and instrument cluster.
- **tesla_hud.js** — Browser-side HUD that connects to the telemetry WebSocket. Auto-falls back to demo mode if the pipeline isn't running.
- **telemetry_server.py** — WebSocket server streaming pipeline results at ~20 Hz to connected HUD clients.

## Usage

1. Run the telemetry server: `python hud/telemetry_server.py`
2. Open `tesla_hud.js` in Tesla's browser (or serve it via the car's local network)
3. The HUD renders live hazard markers, evasion directions, and path decisions.

## Tesla Integration Notes

- Tesla's browser supports standard HTML5/SVG — no native app needed
- The HUD overlays Tesla's native UI; it does not interfere with Autopilot rendering
- For production, serve via the car's local Wi-Fi or a Tesla Theater app
- Display geometry is approximate and varies by model (Model 3/Y vs S/X)

## Safety

This is a perception and display layer only. It does not control steering,
braking, or acceleration. Any actuation would require Tesla's official
API access and proper safety validation.