"""Per-transcript narrative theme extraction.

Scans earnings-call transcripts (stored under data/transcripts/) for
management commentary on five strategic themes —

    supply       tight        ↔  easing
    demand       strong       ↔  weak
    capex        raised       ↔  cut
    lead_times   extending    ↔  shortening
    pricing      rising       ↔  pressure

Each theme mention is one sentence containing a theme noun ("supply",
"demand", "capex", "lead time", "ASP", ...). Tone is determined by the
presence of polarity modifiers in the same sentence. If neither
polarity appears we record the mention as "neutral" (the management
brought up the topic without a directional signal).

The convention is: POSITIVE = the management narrative supports the
bottleneck thesis (tight supply, strong demand, rising capex, extending
lead times, rising prices). NEGATIVE = the thesis is weakening. This
makes a single +/- score per theme directly comparable across quarters.

Output: data/narrative_tracking.json
  {
    "generated_at": iso,
    "by_ticker": {
      "<TICKER>": [        # list of calls, newest-first
        {
          "call_id": int,
          "date": "YYYY-MM-DD",
          "call_type": "...",
          "url": "...",
          "themes": {
            "<theme>": {
              "mentions": int,
              "tone_score": float,        # (pos - neg) / max(1, pos + neg)
              "counts": {"positive": n, "negative": n, "neutral": n},
              "quotes": [ {tone, speaker, role, text} ]   # cap 5
            }
          }
        }
      ]
    },
    "summary": { ... }
  }

Subsequent quarters' transcripts append to each ticker's list. The frontend reads
this file to render narrative-drift sparklines on stock.html (task #5).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

log = logging.getLogger(__name__)

# Themes carry (theme_terms, positive_terms, negative_terms). All terms
# are matched case-insensitively as substrings on a normalized sentence.
# Positive direction = the bottleneck thesis is reinforced; negative =
# weakening. See module docstring.
THEMES: dict[str, dict[str, list[str]]] = {
    "supply": {
        "terms": [
            "supply", "supplies", "capacity",
        ],
        "positive": [
            "allocated", "allocation", "sold out", "sold-out",
            "supply constrained", "supply-constrained", "constrained",
            "tight", "tightness", "tightening", "shortage", "shortages",
            "backlog", "book-to-bill", "book to bill",
            "capacity-limited", "capacity limited",
            "cannot meet demand", "outstripping supply",
            "demand outpaces supply", "demand exceeds supply",
            "ramp constraint", "supply gap", "scarce", "scarcity",
            "long lead", "stretched",
        ],
        "negative": [
            "easing", "eased", "easier", "loosening", "loosened",
            "normalized", "normalizing", "in balance", "rebalanced",
            "ample", "abundant", "freed up", "freed-up",
            "in line with demand", "caught up", "back in line",
            "supply is good", "improved supply", "improving supply",
        ],
    },
    "demand": {
        "terms": [
            "demand", "order", "orders", "bookings", "pipeline",
            "order book", "backlog", "design wins", "design-wins",
        ],
        "positive": [
            "strong", "robust", "accelerating", "accelerated",
            "increasing", "growing", "surging", "surged",
            "exceeded", "ahead of plan", "outpaced", "outperformed",
            "record", "record-high", "off the charts",
            "stronger than expected", "stronger-than-expected",
            "broad-based", "broad based", "healthy", "elevated",
            "remarkable", "robust demand", "demand remains strong",
        ],
        "negative": [
            "weakening", "weakened", "softening", "softened",
            "weak", "muted", "decelerating", "decelerated",
            "softer", "moderating", "moderated", "slowdown",
            "below expectations", "below-expectations",
            "lower demand", "demand is lower", "tepid", "sluggish",
            "pushed out", "push-out", "pause", "paused",
        ],
    },
    "capex": {
        "terms": [
            "capex", "capital expenditure", "capital expenditures",
            "capital investment", "capital investments",
            "capital spending", "capital intensity",
        ],
        "positive": [
            "raised", "raising", "increased", "increasing",
            "higher", "expand", "expanded", "expanding",
            "boosted", "boosting", "upped", "stepping up",
            "stepping-up", "ramping up", "ramp-up", "elevated",
            "above prior", "above plan", "ahead of plan",
            "up year-over-year", "up year over year", "up yoy",
            "record capex", "incremental capex",
        ],
        "negative": [
            "cut", "cutting", "reduced", "reducing", "lower",
            "trim", "trimmed", "trimming", "lowering",
            "scaled back", "scale back", "scaling back",
            "slowed", "slowing", "moderating", "moderated",
            "below prior", "below plan", "deferred", "delayed",
            "down year-over-year", "down yoy",
        ],
    },
    "lead_times": {
        "terms": [
            "lead time", "lead-time", "lead times", "lead-times",
            "delivery time", "delivery times",
        ],
        "positive": [
            "extending", "extended", "lengthening", "lengthened",
            "longer", "stretched", "stretching", "growing",
            "elongated", "have grown", "are growing",
        ],
        "negative": [
            "shortening", "shortened", "shorter", "improving",
            "improved", "normalized", "normalizing",
            "in line", "back to normal", "compressed",
        ],
    },
    "pricing": {
        "terms": [
            "price", "prices", "pricing", "asp", "asps",
            "average selling price", "average sales price",
            "average selling prices", "price per",
        ],
        "positive": [
            "rising", "higher", "increase", "increased",
            "increasing", "up year-over-year", "up year over year",
            "pricing power", "premium", "command higher",
            "strong pricing", "favorable pricing", "raised price",
            "price increase",
        ],
        "negative": [
            "lower", "pressure", "pressured", "compression",
            "compressed", "discount", "discounting", "discounted",
            "rolled back", "rollback", "competitive pricing",
            "price decline", "declined", "asp decline",
            "price erosion",
        ],
    },
}

# Sentence splitter. Collapse \r\n, then split on . ! ? ; followed by space/EOL.
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+")
_WS_RE = re.compile(r"\s+")
# Max quotes to keep per (call, theme) in the output JSON.
QUOTES_PER_THEME = 5
# Skip extremely short sentences — they almost always lack context.
MIN_SENTENCE_CHARS = 25


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text.replace("\r", " ").replace("\n", " ")).strip()


def _split_sentences(text: str) -> list[str]:
    norm = _normalize(text)
    return [s.strip() for s in _SENT_SPLIT_RE.split(norm) if s.strip()]


def _contains_any(haystack_lower: str, terms: Iterable[str]) -> bool:
    return any(t in haystack_lower for t in terms)


def _classify_sentence(sentence_lower: str) -> dict[str, str]:
    """Return {theme: tone} for every theme triggered by this sentence."""
    out: dict[str, str] = {}
    for theme, lex in THEMES.items():
        if not _contains_any(sentence_lower, lex["terms"]):
            continue
        pos = _contains_any(sentence_lower, lex["positive"])
        neg = _contains_any(sentence_lower, lex["negative"])
        if pos and not neg:
            out[theme] = "positive"
        elif neg and not pos:
            out[theme] = "negative"
        elif pos and neg:
            # Ambiguous — prefer negative (a "but" or "however" usually
            # flips the headline tone toward the qualifier).
            out[theme] = "negative"
        else:
            out[theme] = "neutral"
    return out


def _empty_theme_bucket() -> dict:
    return {
        "mentions": 0,
        "tone_score": 0.0,
        "counts": {"positive": 0, "negative": 0, "neutral": 0},
        "quotes": [],
    }


def _analyze_call(entry: dict) -> dict:
    """Compute per-theme counts and pick top quotes for one transcript."""
    themes: dict[str, dict] = {t: _empty_theme_bucket() for t in THEMES}
    for seg in entry.get("segments") or []:
        text = seg.get("text") or ""
        if not text:
            continue
        speaker = seg.get("speaker")
        role = seg.get("role")
        for sentence in _split_sentences(text):
            if len(sentence) < MIN_SENTENCE_CHARS:
                continue
            classified = _classify_sentence(sentence.lower())
            for theme, tone in classified.items():
                bucket = themes[theme]
                bucket["mentions"] += 1
                bucket["counts"][tone] += 1
                # Keep up to QUOTES_PER_THEME; prefer pos/neg over neutral.
                if len(bucket["quotes"]) < QUOTES_PER_THEME:
                    bucket["quotes"].append({
                        "tone": tone,
                        "speaker": speaker,
                        "role": role,
                        "text": sentence[:400],
                    })
                else:
                    # Replace the oldest neutral with a directional sentence
                    # so directional evidence wins ties.
                    if tone != "neutral":
                        for i, q in enumerate(bucket["quotes"]):
                            if q["tone"] == "neutral":
                                bucket["quotes"][i] = {
                                    "tone": tone,
                                    "speaker": speaker,
                                    "role": role,
                                    "text": sentence[:400],
                                }
                                break

    for theme, bucket in themes.items():
        pos = bucket["counts"]["positive"]
        neg = bucket["counts"]["negative"]
        denom = max(1, pos + neg)
        bucket["tone_score"] = round((pos - neg) / denom, 3)

    return themes


def compute(transcripts_dir: Path) -> dict:
    """Scan every transcript JSON under `transcripts_dir` and return the
    aggregated narrative-tracking dict."""
    by_ticker: dict[str, list[dict]] = {}
    total_mentions = 0
    calls_analyzed = 0

    if not transcripts_dir.exists():
        log.warning("No transcripts dir at %s — nothing to analyze", transcripts_dir)
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "by_ticker": {},
            "summary": {"calls_analyzed": 0, "tickers_covered": 0, "total_mentions": 0},
        }

    for p in sorted(transcripts_dir.glob("*.json")):
        try:
            entry = json.loads(p.read_text())
        except Exception as e:
            log.warning("Skip %s: %s", p.name, e)
            continue
        ticker = entry.get("ticker")
        if not ticker:
            continue
        themes = _analyze_call(entry)
        mentions = sum(t["mentions"] for t in themes.values())
        total_mentions += mentions
        calls_analyzed += 1
        by_ticker.setdefault(ticker, []).append({
            "call_id": entry.get("call_id"),
            "date": entry.get("date"),
            "call_type": entry.get("call_type"),
            "url": entry.get("url"),
            "themes": themes,
            "mentions_total": mentions,
        })

    # Newest-first within each ticker.
    for t, calls in by_ticker.items():
        calls.sort(key=lambda c: c.get("date") or "", reverse=True)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "by_ticker": by_ticker,
        "summary": {
            "calls_analyzed": calls_analyzed,
            "tickers_covered": len(by_ticker),
            "total_mentions": total_mentions,
            "themes": list(THEMES.keys()),
        },
    }
