---
name: Inference Stack Dashboard project
description: Static HTML + Python data layer dashboard at /Users/alex/alexthegreat/Inference-Dashboard mapping 15 layers of the AI inference stack.
type: project
originSessionId: 9f9b2939-5573-4589-a8b5-8c3caa2e4019
---
Built `/Users/alex/alexthegreat/Inference-Dashboard` — a personal investing dashboard for AI inference scaling bottlenecks. Static HTML frontend, Python data layer, free-tier sources only (yfinance, EDGAR, RSS).

**Why:** User wanted to map the full inference stack and identify under-priced layers (memory has run; what's next?).

**How to apply:** Future sessions on this project — read `CLAUDE.md` in the project root for the navigation guide. Source of truth for layers/players/curated signals lives in `jobs/seed.py`. Daily refresh via `python -m jobs.refresh` or double-click `refresh.command`.

Earnings-call narrative tracking is live as of 2026-05-13:
  - `jobs/sources/transcripts.py` pulls latest call per ticker from earningscalls.dev (48/65 coverage, see [[reference-transcripts-source]])
  - `jobs/narrative.py` extracts per-call tone scores across 5 themes (supply/demand/capex/lead-times/pricing) → `data/narrative_tracking.json`
  - `jobs/sources/transcripts_extract.py` mines exec quotes into the signals feed (transcript-* IDs)
  - "Management narrative drift" section on `stock.html` shows per-theme tone bar + dot sparkline (one dot per call; fills in as quarters accumulate). Empty-state for non-US gaps explains the limitation.

Lexicon tuning notes for the narrative extractor (open work, low priority):
  - TSM "supply" tone has a few false-negatives where "capacity" matches in gross-margin discussions. Either tighten the supply theme terms (drop bare "capacity"; require "capacity-constrained"/"capacity-limited"-style phrasing) or expand the ambiguous-tone disambiguation.
  - Single-sentence windows occasionally miss tone modifiers in the next sentence. 2-sentence sliding window is the obvious upgrade if false-negatives bite.

Pending: enrich Optics layer with CPO (co-packaged optics) sub-theme and CPO-positioning for LITE/COHR/MRVL/AVGO. User explicitly said "we can do that in the next session."
