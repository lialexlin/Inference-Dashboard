"""Auto-generate cross_quarter.json supply-tightness entries from filings.

The hand-written entries (e.g. MU, NVDA) carry rich narrative — headline,
multi-area shifts list, verdict. The auto-generator can't match that quality.
What it CAN do is extract the binary supply-tightness signal across two
consecutive filings, which is exactly what `bottleneck.py` reads to flag
`cross_quarter_supply_tight=True` per layer. That single bit is the
highest-value contribution to the heat-map from this stage.

Behaviour:
  - Group filing_summaries by ticker, newest-first by filed_date
  - For each ticker with ≥2 filings within MAX_AGE_DAYS:
      - Detect supply-tightness language in each filing's combined text
      - If both tight (no easing) → emit area=supply direction=tight shift
      - If new tightness in latest only → emit "tight" (less confident)
      - If easing replaced tightness → emit area=supply direction=easing
  - Preserve any manually-written entry (no auto_generated flag) as-is —
    manual narrative wins because it has verdict/headline context the
    generator can't fabricate.

Output entries carry `auto_generated: true` so the UI / user can
distinguish them from manual entries.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

# Stricter than bottleneck.py's lexicon — these are compound phrases that
# unambiguously denote demand-exceeds-supply, not isolated tokens that fire
# on SaaS RPO ("backlog") or financial metric language ("tight", "constrained").
TIGHTNESS_TERMS: list[str] = [
    "demand exceeds supply", "demand outpaces supply", "demand far exceeds",
    "outstripping supply", "cannot meet demand",
    "supply allocation", "supply constrained", "supply-constrained",
    "supply gap", "supply-gap",
    "capacity constrained", "capacity-constrained",
    "capacity limited", "capacity-limited",
    "sold out", "sold-out",
    "tight supply", "tight conditions",
    "shortage",
    "allocation decisions",
    "lead times extending", "extending lead times", "longer lead times",
    "ramp constraint",
]
EASING_TERMS: list[str] = [
    "supply easing", "supply has eased", "supply normalized", "supply normalizing",
    "demand has weakened", "demand softening", "demand softened",
    "in balance", "rebalanced", "ample supply", "abundant supply",
    "freed-up capacity", "in line with demand",
    "lead times shortening", "shorter lead times", "lead times improving",
]
MAX_AGE_DAYS = 400
LATEST_N_FILINGS = 2


def _filing_text(summ: dict) -> str:
    parts = [
        summ.get("tldr") or "",
        summ.get("quote") or "",
        *(summ.get("takeaways") or []),
    ]
    g = summ.get("guidance") or {}
    for v in g.values():
        if isinstance(v, str):
            parts.append(v)
    return " ".join(parts).lower()


def _has_term(text: str, terms: list[str]) -> bool:
    return any(t in text for t in terms)


def generate(filing_summaries: dict, manual_entries: dict | None = None) -> dict:
    """Build cross_quarter dict from filing_summaries.

    `manual_entries` (typically the subset of an existing cross_quarter.json
    that lacks `auto_generated: true`) is preserved as-is; auto entries fill
    in tickers not covered manually.
    """
    manual_entries = manual_entries or {}
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for summ in filing_summaries.values():
        if not isinstance(summ, dict):
            continue
        if not summ.get("ticker") or not summ.get("filed_date"):
            continue
        by_ticker[summ["ticker"]].append(summ)
    for lst in by_ticker.values():
        lst.sort(key=lambda s: s.get("filed_date") or "", reverse=True)

    today = datetime.now(timezone.utc).date()
    out: dict[str, dict] = dict(manual_entries)

    for ticker, filings in by_ticker.items():
        if ticker in out:
            continue
        latest = filings[:LATEST_N_FILINGS]
        if len(latest) < 2:
            continue
        try:
            d = datetime.strptime(latest[0]["filed_date"], "%Y-%m-%d").date()
        except (ValueError, KeyError, TypeError):
            continue
        if (today - d).days > MAX_AGE_DAYS:
            continue

        tight = [_has_term(_filing_text(f), TIGHTNESS_TERMS) for f in latest]
        easing = [_has_term(_filing_text(f), EASING_TERMS) for f in latest]

        shifts: list[dict] = []
        if all(tight) and not any(easing):
            shifts.append({
                "area": "supply",
                "direction": "tight",
                "trend": "Supply-tightness language present in both latest filings",
                "note": "auto-derived from filing keyword presence",
            })
        elif tight[0] and not tight[1]:
            shifts.append({
                "area": "supply",
                "direction": "tight",
                "trend": "Latest filing introduces tightness language absent from prior",
                "note": "auto-derived (new tightness — single-quarter, lower confidence)",
            })
        elif easing[0] and tight[1]:
            shifts.append({
                "area": "supply",
                "direction": "easing",
                "trend": "Latest filing shows easing language vs prior-quarter tightness",
                "note": "auto-derived (easing)",
            })

        if not shifts:
            continue

        accessions = [f.get("accession") for f in latest if f.get("accession")]
        out[ticker] = {
            "as_of": today.isoformat(),
            "auto_generated": True,
            "covers": f"{latest[1]['filed_date']} → {latest[0]['filed_date']}",
            "based_on_accessions": accessions,
            "shifts": shifts,
            "headline": None,
            "verdict": None,
        }

    return out
