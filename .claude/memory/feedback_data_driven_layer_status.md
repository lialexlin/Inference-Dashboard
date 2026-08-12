---
name: feedback-data-driven-layer-status
description: "Inference Dashboard — layer status (and similar rollup labels) must be derived from the scoring data, not from hand-typed editorial values in seed.py"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 24f4dd01-0bf1-4a62-afe3-75a251764fa8
---

Layer status badges on the Inference Dashboard must be data-driven (from `jobs/scoring.py`'s `_layer_status_from_quadrants` rollup of player quadrants). Never reintroduce a `"status": "..."` literal in `jobs/seed.py:LAYERS` as a fallback for the rendered badge.

**Why:** The user noticed Advanced Packaging was showing "underappreciated" when the underlying tickers (ASX/AMKR/2449.TW) were all fair/avoid/priced-in. Root cause was a hand-typed `status` in `seed.py` that fell through the chain `override or auto or seed_status or "fair"` because `status_auto` was None. The user explicitly said: "it should be driven by data, not manual overwrite."

**How to apply:**
- The fallback chain is now `override or auto or "fair"` — no seed fallback. Keep it that way.
- `status_note` (editorial commentary, ~1 sentence per layer) is fine to keep in seed.py — it's displayed as italic prose, not as a badge.
- `status_override` is the documented escape hatch for explicit pins (e.g., "data says X but I know better"). Currently unused; keep the mechanism but don't pre-populate it.
- If a layer rollup looks wrong, fix the threshold (`THRESH`, `ROLL_*_FRACTION` in [[project-inference-dashboard]]'s `jobs/scoring.py`) or the component weights, not the seed.
- `jobs/seed.py:main()` now preserves `status_auto`/`status` from prior `data/layers.json` when rewriting — don't remove that preservation, or seed reruns will stomp the scoring output again.
