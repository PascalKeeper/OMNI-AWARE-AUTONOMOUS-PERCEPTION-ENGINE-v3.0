"""Tesla HUD overlay for OMNI-AWARE v3.0.

Renders hazard markers, evasion arrows, and decision banners
on Tesla's 17-inch center display and instrument cluster.
Designed to overlay the existing Tesla UI without interfering
with Autopilot's native rendering.
"""
import math

# Tesla display geometry (approximate, varies by model)
CENTER_DISPLAY = {"width": 1920, "height": 1200}   # Model 3/Y 17"
CLUSTER = {"width": 1920, "height": 720}          # instrument cluster

# Colors (Tesla UI palette)
COLORS = {
    "boulder": "#FF5252",
    "log": "#FFAB40",
    "debris": "#FFEB3B",
    "cliff": "#FF1744",
    "waterfall": "#4FC3F7",
    "safe": "#00E676",
    "text": "#E0E0E0",
    "bg": "#0A0A0F",
}


class TeslaHUD:
    """HUD renderer for Tesla center display and cluster."""

    def __init__(self, display="center"):
        self.display = display
        self.geom = CENTER_DISPLAY if display == "center" else CLUSTER
        self.hazards = []
        self.decision = None
        self.evasion = None

    def update(self, hazards: list, decision: dict = None, evasion: str = None):
        """Update HUD state from pipeline results."""
        self.hazards = hazards
        self.decision = decision
        self.evasion = evasion

    def render_svg(self) -> str:
        """Render current state as SVG for the Tesla browser."""
        W, H = self.geom["width"], self.geom["height"]
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" style="background:{COLORS["bg"]}">']

        # hazard markers
        for h in self.hazards:
            color = COLORS.get(h.get("type", "debris"), COLORS["debris"])
            x, y = h.get("x", W // 2), h.get("y", H // 2)
            r = h.get("size", 20)
            parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="0.5"/>')
            parts.append(f'<circle cx="{x}" cy="{y}" r="{r//2}" fill="{color}"/>')
            parts.append(f'<text x="{x}" y="{y - r - 8}" fill="{COLORS["text"]}" font-size="14" text-anchor="middle">{h.get("type", "?").upper()}</text>')

        # evasion arrow
        if self.evasion and "left" in self.evasion:
            parts.append(self._arrow(W // 2 - 100, H // 2, -1, COLORS["safe"]))
        elif self.evasion and "right" in self.evasion:
            parts.append(self._arrow(W // 2 + 100, H // 2, 1, COLORS["safe"]))
        elif self.evasion and "brake" in self.evasion:
            parts.append(f'<rect x="{W//2-60}" y="{H//2-30}" width="120" height="60" fill="{COLORS["cliff"]}" opacity="0.7" rx="8"/>')
            parts.append(f'<text x="{W//2}" y="{H//2+8}" fill="{COLORS["text"]}" font-size="20" text-anchor="middle">BRAKE</text>')

        # decision banner
        if self.decision:
            choice = self.decision.get("choice", "")
            color = COLORS.get(choice, COLORS["text"])
            parts.append(f'<rect x="{W//2-200}" y="40" width="400" height="60" fill="{color}" opacity="0.3" rx="8"/>')
            parts.append(f'<text x="{W//2}" y="78}" fill="{color}" font-size="24" font-weight="bold" text-anchor="middle">{choice.upper()}</text>')

        parts.append("</svg>")
        return "\n".join(parts)

    def _arrow(self, x, y, direction, color):
        """Draw an evasion arrow pointing left (-1) or right (1)."""
        d = direction
        tip_x = x + d * 60
        return (
            f'<line x1="{x}" y1="{y}" x2="{tip_x}" y2="{y}" stroke="{color}" stroke-width="6"/>'
            f'<polygon points="{tip_x},{y} {tip_x - d*20},{y-15} {tip_x - d*20},{y+15}" fill="{color}"/>'
        )

    def render_html_page(self) -> str:
        """Full HTML page for Tesla's browser (center display)."""
        svg = self.render_svg()
        return f"<!DOCTYPE html>\n<html><head><meta charset='UTF-8'><title>OMNI-AWARE HUD</title></head><body style='margin:0'>{svg}</body></html>"


if __name__ == "__main__":
    hud = TeslaHUD(display="center")
    hud.update(
        hazards=[{"type": "boulder", "x": 960, "y": 600, "size": 40}],
        decision={"choice": "waterfall", "score": 2.83},
        evasion="veer left",
    )
    print(hud.render_svg()[:500])
    print("...")
    print(f"Full page: {len(hud.render_html_page())} bytes")