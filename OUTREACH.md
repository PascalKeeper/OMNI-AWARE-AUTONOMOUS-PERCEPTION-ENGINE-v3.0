# Outreach Templates

Use these when applying or reaching out. Customize the bracketed parts.

---

## Tesla — Autonomy / Perception / Test Engineering

**Subject:** Perception prototype with safety case — open to feedback

Hi [Name],

I'm a software engineer who built an autonomous perception prototype from scratch over the past several months. It's not production code, and I'm not claiming it is — but I think the way it's built might be worth a look.

The repo (github.com/PascalKeeper/OMNI-AWARE-AUTONOMOUS-PERCEPTION-ENGINE-v3.0) includes:

- A full perception pipeline: RGB spectrum filter, quadrant-split sensor processing, RANSAC outlier rejection, sensor fusion with staged detection ranges, predictive braking, map-aware speed advisories, and a traction loop that cross-references wheel slip, visual surface cues, and acoustic tire noise.
- A safety case documenting every claim, every limitation, and the mitigation for each — including where the system would fail (color-critical signals, highway braking distances, nighttime pedestrians).
- Honest benchmarks: a simulated detector scores F1 0.981 (proving the eval protocol), while the real pipeline scores F1 0.722 with precision 0.920 and recall 0.593. The recall gap is traced to specific failure modes with documented fixes.
- A C++ reference port with an HW4-style performance mock showing the algorithms are portable and that the Python baseline (82 FPS) was an interpreter ceiling, not an algorithm ceiling.

What I'm looking for: feedback on the architecture, and a conversation about where someone who thinks this way fits on the team — test engineering, data operations, or perception tooling are all interesting to me.

I'm not asking you to hire me from a cold message. I'm asking for ten minutes if any of this resonates.

Thanks,
[Your name]

---

## xAI — Grok / Applied Research / Engineering

**Subject:** Perception engine built with Grok — full lineage in one repo

Hi [Name],

I built an autonomous perception prototype using Grok as my coding partner — every commit, every design decision, and every failure mode is in the repo. I wanted to share it because the process might be as interesting as the result.

The repo (github.com/PascalKeeper/OMNI-AWARE-AUTONOMOUS-PERCEPTION-ENGINE-v3.0) shows:

- Iterative development across six versions (v0.9.4 through v1.2.0-GOLD), with the full lineage preserved so nothing is lost between iterations.
- A Grok API integration with automatic fallback to local heuristics when the API is unavailable — the pipeline never stalls.
- A safety case and benchmark protocol that treat honest measurement as the product, not the demo.

I'm interested in roles where building with AI tooling is the norm, not the exception — and where the ability to document what a system cannot do matters as much as what it can.

Open to a conversation if this is useful.

[Your name]

---

## Tips

- Send to a specific person, not a general inbox. Find the hiring manager or a senior engineer on the team via LinkedIn.
- Attach or link the ONE_PAGER.md — it's the two-minute read.
- Don't lead with the 422 FPS number. Lead with the safety case and the honest benchmark gap.
- Follow up once after 7-10 days. Silence is normal; persistence is fine.
- If you get a response, the repo is your proof. Be ready to walk through any file.