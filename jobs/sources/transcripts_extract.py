"""Mine management Q&A quotes from on-disk transcripts into signal entries.

Reads data/transcripts/*.json (written by jobs/sources/transcripts.py).
For each transcript:
  - Filter to executive-speaker segments (skips operator and analyst questions)
  - Score each segment by supply-tightness + capex/scale language
  - If no segment scores > 0: skip (transcript carries no useful signal)
  - Otherwise emit one signal entry with the top quote and a few takeaways

Output signal shape matches what transform.tag() and bottleneck.compute()
already consume. Source_type="earnings". IDs are stable across runs:
`transcript-{ticker}-{call_id}` — call_id is earningscalls.dev's integer key.

This runs independently of the network fetch — it operates on on-disk
transcripts only, so it works even when --skip-transcripts is set or the
upstream service is down.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

# Supply-tightness lexicon — same definition of "binding constraint" used by
# bottleneck.py, kept local so this module is dependency-free.
TIGHTNESS_TERMS: list[str] = [
    "allocated", "allocation", "sold out", "sold-out",
    "lead time", "lead-time",
    "supply constrained", "supply-constrained", "constrained",
    "shortage", "backlog", "book-to-bill", "book to bill",
    "capacity-limited", "capacity limited",
    "cannot meet demand", "outstripping supply",
    "demand outpaces supply", "demand exceeds supply",
    "demand far exceeds", "ramp constraint", "supply gap",
    "tight supply", "tight conditions", "tight",
]

# Demand / capex / scale language — the other half of management commentary
# that signals which layer is binding.
DEMAND_TERMS: list[str] = [
    "raised guidance", "raise our guidance", "raising our guidance",
    "guide higher", "guide up", "above plan", "record",
    "gigawatt", " gw of ", "multi-year agreement", "long-term agreement",
    "training cluster", "inference workload",
    "demand for", "robust demand", "strong demand",
    "capex", "capital expenditure",
]

SCORE_TERMS: list[str] = TIGHTNESS_TERMS + DEMAND_TERMS

MIN_SEGMENT_WORDS = 25      # drops "Maybe..." / "Yes." / one-line redirects
QUOTE_MAX_CHARS = 380
TAKEAWAY_MAX_CHARS = 220
TOP_TAKEAWAYS = 3


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower())


def _score_segment(text: str) -> int:
    norm = _normalize(text)
    return sum(1 for t in SCORE_TERMS if t in norm)


def _truncate(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    # Prefer sentence boundary if it's at least 60% of the way through
    last_period = cut.rfind(". ")
    if last_period >= max_chars * 0.6:
        return cut[: last_period + 1].rstrip()
    return cut.rstrip() + "…"


def _is_executive(role: str | None) -> bool:
    if not role:
        return False
    r = role.lower()
    return ("exec" in r) or ("ceo" in r) or ("cfo" in r) or ("management" in r)


def extract_from_transcript(entry: dict) -> dict | None:
    """Produce one signal dict from a parsed transcript, or None if no useful signal.

    A transcript is dropped (returns None) when no executive segment contains
    any supply/demand language — better to be silent than emit noise.
    """
    ticker = entry.get("ticker")
    call_id = entry.get("call_id")
    if not ticker or call_id is None:
        return None
    segments = entry.get("segments") or []

    scored: list[tuple[int, dict]] = []
    for seg in segments:
        text = seg.get("text") or ""
        if len(text.split()) < MIN_SEGMENT_WORDS:
            continue
        if not _is_executive(seg.get("role")):
            continue
        s = _score_segment(text)
        if s > 0:
            scored.append((s, seg))

    if not scored:
        return None

    scored.sort(key=lambda t: -t[0])
    top_score, top_seg = scored[0]

    quote = _truncate(top_seg.get("text") or "", QUOTE_MAX_CHARS)
    speaker = top_seg.get("speaker") or "?"
    role = top_seg.get("role") or "?"

    takeaways: list[str] = []
    seen_keys: set[str] = {quote[:60]}
    for _, seg in scored[1:]:
        t = _truncate(seg.get("text") or "", TAKEAWAY_MAX_CHARS)
        key = t[:60]
        if key in seen_keys:
            continue
        seen_keys.add(key)
        sp = seg.get("speaker") or "?"
        takeaways.append(f"[{sp}] {t}")
        if len(takeaways) >= TOP_TAKEAWAYS:
            break

    call_type = entry.get("call_type") or "Earnings Call"

    return {
        "id": f"transcript-{ticker}-{call_id}",
        "date": entry.get("date"),
        "headline": f"{ticker} {call_type}",
        "source": "earningscalls.dev",
        "source_type": "earnings",
        "url": entry.get("url"),
        "quote": f"[{speaker}, {role}] {quote}",
        "tickers": [ticker],
        "layer_ids": [],
        "summary": {
            "tldr": f"Top-scoring management Q&A from {entry.get('date') or '?'}.",
            "takeaways": takeaways,
            "score": top_score,
            "speaker": speaker,
            "role": role,
        },
    }


def build_signals(transcripts_dir: Path) -> list[dict]:
    """Scan transcripts_dir/*.json; emit one signal per transcript with score>0."""
    out: list[dict] = []
    if not transcripts_dir.exists():
        return out
    for path in sorted(transcripts_dir.glob("*.json")):
        try:
            entry = json.loads(path.read_text())
        except Exception as e:
            log.warning("Skip transcript %s: %s", path.name, e)
            continue
        sig = extract_from_transcript(entry)
        if sig is not None:
            out.append(sig)
    return out
