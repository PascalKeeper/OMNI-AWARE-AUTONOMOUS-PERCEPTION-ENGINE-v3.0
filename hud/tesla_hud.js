/**
 * Tesla HUD overlay — OMNI-AWARE v3.0
 *
 * Runs in Tesla's browser (center display). Connects to the
 * perception pipeline via WebSocket for live hazard telemetry.
 * Renders SVG overlay: hazard markers, evasion arrows, decision banner.
 */

const WS_URL = 'ws://localhost:8765';  // pipeline telemetry endpoint

const COLORS = {
  boulder: '#FF5252', log: '#FFAB40', debris: '#FFEB3B',
  cliff: '#FF1744', waterfall: '#4FC3F7', safe: '#00E676', text: '#E0E0E0'
};

class TeslaHUD {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.hazards = [];
    this.decision = null;
    this.evasion = null;
    this.ws = null;
    this.connect();
  }

  connect() {
    try {
      this.ws = new WebSocket(WS_URL);
      this.ws.onmessage = (e) => this.onTelemetry(JSON.parse(e.data));
      this.ws.onclose = () => setTimeout(() => this.connect(), 2000);
    } catch (err) {
      console.log('WS unavailable, using demo mode');;
      this.demoMode();
    }
  }

  onTelemetry(data) {
    this.hazards = data.hazards || [];
    this.decision = data.decision || null;
    this.evasion = data.evasion || null;
    this.render();
  }

  demoMode() {
    // synthetic hazard stream for testing without the pipeline
    setInterval(() => {
      if (Math.random() > 0.7) {
        this.hazards.push({
          type: Math.random() > 0.5 ? 'boulder' : 'log',
          x: 400 + Math.random() * 1120,
          y: 300 + Math.random() * 600,
          size: 20 + Math.random() * 40
        });
        if (this.hazards.length > 5) this.hazards.shift();
      }
      this.render();
    }, 500);
  }

  render() {
    const W = this.container.clientWidth || 1920;
    const H = this.container.clientHeight || 1200;
    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" style="background:#0A0A0F">`;

    for (const h of this.hazards) {
      const c = COLORS[h.type] || COLORS.debris;
      svg += `<circle cx="${h.x}" cy="${h.y}" r="${h.size}" fill="${c}" opacity="0.5"/>`;
      svg += `<circle cx="${h.x}" cy="${h.y}" r="${h.size/2}" fill="${c}"/>`;
      svg += `<text x="${h.x}" y="${h.y - h.size - 8}" fill="${COLORS.text}" font-size="14" text-anchor="middle">${h.type.toUpperCase()}</text>`;
    }

    if (this.evasion && this.evasion.includes('left')) {
      svg += this.arrow(W/2 - 100, H/2, -1, COLORS.safe);
    } else if (this.evasion && this.evasion.includes('right')) {
      svg += this.arrow(W/2 + 100, H/2, 1, COLORS.safe);
    } else if (this.evasion && this.evasion.includes('brake')) {
      svg += `<rect x="${W/2-60}" y="${H/2-30}" width="120" height="60" fill="${COLORS.cliff}" opacity="0.7" rx="8"/>`;
      svg += `<text x="${W/2}" y="${H/2+8}" fill="${COLORS.text}" font-size="20" text-anchor="middle">BRAKE</text>`;
    }

    if (this.decision) {
      const c = COLORS[this.decision.choice] || COLORS.text;
      svg += `<rect x="${W/2-200}" y="40" width="400" height="60" fill="${c}" opacity="0.3" rx="8"/>`;
      svg += `<text x="${W/2}" y="78" fill="${c}" font-size="24" font-weight="bold" text-anchor="middle">${this.decision.choice.toUpperCase()}</text>`;
    }

    svg += '</svg>';
    this.container.innerHTML = svg;
  }

  arrow(x, y, d, color) {
    const tip = x + d * 60;
    return `<line x1="${x}" y1="${y}" x2="${tip}" y2="${y}" stroke="${color}" stroke-width="6"/>`
      + `<polygon points="${tip},${y} ${tip-d*20},${y-15} ${tip-d*20},${y+15}" fill="${color}"/>`;
  }
}

// Auto-init when loaded in Tesla browser
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new TeslaHUD('hud'));
} else {
  new TeslaHUD('hud'));
}