"""Codified exit-trigger states for the bottleneck-rotation thesis.

The user's framework hinges on knowing *when to sell*. These four triggers
are the thesis-killers; this stage evaluates each into green / amber / red
and surfaces the supporting evidence so the decision can be made on data
under stress (not rationalized away).

The four triggers (from the framework):
  1. token_growth      — frontier inference token-throughput WoW growth
  2. hyperscaler_capex — major hyperscaler cutting capex guide
  3. arch_risk         — algorithmic shift collapsing FLOPs/token
  4. taiwan            — geopolitical Taiwan break (manual override)

Output: data/exit_triggers.json
{
  "as_of": "2026-05-13T...",
  "triggers": {
    "token_growth": {"state": "green|amber|red", "evidence": [...], "rule": "..."},
    "hyperscaler_capex": {...},
    "arch_risk": {...},
    "taiwan": {"state": ..., "manual": true, "evidence": [...]}
  },
  "overall": "green|amber|red"   # worst of all four
}

The Taiwan trigger is curated manually in data/exit_triggers_manual.json
(single key: {"taiwan_state": "green|amber|red", "taiwan_note": "..."}).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

WORST_ORDER = {"green": 0, "amber": 1, "red": 2}


def _eval_token_growth(demand_signals: dict | None) -> dict:
    """GREEN: WoW token growth median >= +5%
       AMBER: 0 <= WoW < 5%
       RED:   WoW < 0% for the latest snapshot OR awaiting >7 days of history
              and DoD has been negative consecutively."""
    rule = "Frontier inference WoW token growth: GREEN ≥+5% / AMBER 0–5% / RED negative or history insufficient."
    if not demand_signals or not isinstance(demand_signals, dict):
        return {"state": "amber", "evidence": ["No demand telemetry yet — awaiting OpenRouter history."], "rule": rule}
    summary = demand_signals.get("summary", {}) or {}
    wow = summary.get("wow_pct")
    if wow is None:
        return {"state": "amber",
                "evidence": [f"Awaiting WoW history (latest snapshot {summary.get('latest_date', '?')}, need 7d+ to compute)."],
                "rule": rule}
    if wow >= 0.05:
        state = "green"
    elif wow >= 0:
        state = "amber"
    else:
        state = "red"
    evidence = [f"WoW token-throughput change: {wow * 100:+.1f}% (snapshot {summary.get('latest_date', '?')})"]
    # Movers context
    movers = (summary.get("top_movers_wow") or [])[:2]
    if movers:
        evidence.append("Top WoW share gainers: " + ", ".join(
            f"{m['model'].split('/')[-1][:30]} {m['share_delta'] * 100:+.1f}pp" for m in movers
        ))
    return {"state": state, "evidence": evidence, "rule": rule}


# Capex-cut language to scan recent hyperscaler earnings filings for.
CAPEX_CUT_RE = re.compile(
    r"\b(?:lower(?:ed)? capex|reduce capex|reducing capex|capex moderation|capex (?:cut|pull[\s\-]?back|pause|trimmed?)|capital expenditure (?:cut|reduction)|moderating (?:spending|capex)|spend(?:ing)? (?:cut|reduction)|cut(?:ting)? (?:our )?capex)\b",
    re.IGNORECASE,
)
HYPERSCALER_TICKERS = {"MSFT", "GOOGL", "META", "AMZN"}


def _eval_hyperscaler_capex(signals: list[dict], filing_summaries: dict | None) -> dict:
    """GREEN: 0 hyperscalers showed capex-cut language in last 90d filings
       AMBER: 1 did
       RED:   2+ did"""
    rule = "Hyperscaler capex guide cuts (MSFT/GOOGL/META/AMZN) in last 90d: GREEN 0 / AMBER 1 / RED 2+."
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    hits: dict[str, list[str]] = {t: [] for t in HYPERSCALER_TICKERS}

    # First pass: scan signals for filing entries with capex-cut language
    for sig in signals or []:
        if sig.get("source_type") not in ("filing", "earnings"):
            continue
        try:
            d = datetime.fromisoformat((sig.get("date") or "").replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if d < cutoff:
            continue
        text_parts = [sig.get("headline", "") or "", sig.get("quote", "") or ""]
        summary = sig.get("summary") or {}
        if isinstance(summary, dict):
            text_parts.append(summary.get("tldr") or "")
            for tk in summary.get("takeaways") or []:
                text_parts.append(tk)
            g = summary.get("guidance") or {}
            for v in g.values():
                if isinstance(v, str):
                    text_parts.append(v)
        text = " ".join(text_parts)
        if not CAPEX_CUT_RE.search(text):
            continue
        for ticker in sig.get("tickers") or []:
            if ticker in HYPERSCALER_TICKERS:
                hits[ticker].append(sig.get("headline", "")[:140] or "(no headline)")

    # Second pass: also scan filing_summaries directly (in case some weren't merged into signals)
    for accession, summ in (filing_summaries or {}).items():
        if not isinstance(summ, dict):
            continue
        ticker = summ.get("ticker")
        if ticker not in HYPERSCALER_TICKERS:
            continue
        text = " ".join(filter(None, [
            summ.get("tldr") or "",
            *(summ.get("takeaways") or []),
            *(v if isinstance(v, str) else "" for v in (summ.get("guidance") or {}).values()),
        ]))
        if CAPEX_CUT_RE.search(text):
            already = " ".join(hits[ticker]).lower()
            tldr = (summ.get("tldr") or "")[:140]
            if tldr and tldr.lower() not in already:
                hits[ticker].append(tldr)

    flagged = [t for t, h in hits.items() if h]
    if len(flagged) >= 2:
        state = "red"
    elif len(flagged) == 1:
        state = "amber"
    else:
        state = "green"
    evidence = []
    if flagged:
        for t in flagged:
            evidence.append(f"[{t}] " + hits[t][0])
    else:
        evidence.append("No capex-cut language in MSFT/GOOGL/META/AMZN filings (last 90d).")
    return {"state": state, "evidence": evidence, "rule": rule}


# Phrases that suggest a frontier-scale efficiency breakthrough has shipped.
EFFICIENCY_CLAIM_RE = re.compile(
    r"\b(?:10x|10×|10 ?x|order of magnitude|magnitude reduction|five times|5x|5×)\b.*\b(?:faster|cheaper|less compute|compute reduction|fewer flops|fewer tokens|inference)\b",
    re.IGNORECASE,
)
EFFICIENCY_MILD_RE = re.compile(
    r"\b(?:3x|3×|4x|4×|2x|2×)\s+(?:faster|cheaper|less compute|fewer flops)\b",
    re.IGNORECASE,
)


def _eval_arch_risk(signals: list[dict]) -> dict:
    """GREEN: 0 arch-risk signals in last 30d claim ≥3× efficiency at frontier
       AMBER: at least 1 mild (2–5×) claim
       RED:   at least 1 ≥10× claim"""
    rule = "Arch-risk signals (last 30d): GREEN none / AMBER mild 2–5× efficiency claim / RED ≥10× claim."
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    arch_in_window = [s for s in (signals or [])
                      if s.get("arch_risk") and _signal_in_window(s, cutoff)]
    red_hits, amber_hits = [], []
    for s in arch_in_window:
        text = " ".join([s.get("headline", "") or "", s.get("quote", "") or ""])
        if EFFICIENCY_CLAIM_RE.search(text):
            red_hits.append(s.get("headline", "")[:160])
        elif EFFICIENCY_MILD_RE.search(text):
            amber_hits.append(s.get("headline", "")[:160])
    if red_hits:
        return {"state": "red", "evidence": red_hits[:3], "rule": rule}
    if amber_hits:
        return {"state": "amber", "evidence": amber_hits[:3], "rule": rule}
    evidence = [f"{len(arch_in_window)} arch-risk signals in last 30d — none claim a frontier-scale efficiency breakthrough."]
    if arch_in_window:
        evidence.append("Recent arch-risk headlines: " + "; ".join(
            (s.get("headline", "") or "")[:80] for s in arch_in_window[:2]
        ))
    return {"state": "green", "evidence": evidence, "rule": rule}


def _signal_in_window(s: dict, cutoff: datetime) -> bool:
    try:
        d = datetime.fromisoformat((s.get("date") or "").replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d >= cutoff
    except Exception:
        return False


def _eval_taiwan(manual: dict | None) -> dict:
    """Always-manual. Reads exit_triggers_manual.json for the current state."""
    rule = "Taiwan geopolitical break — manually toggled. Set in data/exit_triggers_manual.json."
    manual = manual or {}
    state = manual.get("taiwan_state") or "green"
    if state not in ("green", "amber", "red"):
        state = "amber"
    note = manual.get("taiwan_note") or ""
    evidence = []
    if note:
        evidence.append(note)
    else:
        evidence.append({
            "green": "No active escalation flagged by user.",
            "amber": "Elevated tensions; thesis-watch.",
            "red": "Active disruption — supply chain compromised.",
        }[state])
    return {"state": state, "evidence": evidence, "rule": rule, "manual": True}


def compute(
    signals: list[dict],
    demand_signals: dict | None,
    filing_summaries: dict | None,
    manual: dict | None,
) -> dict:
    triggers = {
        "token_growth": _eval_token_growth(demand_signals),
        "hyperscaler_capex": _eval_hyperscaler_capex(signals, filing_summaries),
        "arch_risk": _eval_arch_risk(signals),
        "taiwan": _eval_taiwan(manual),
    }
    # Overall = worst of all four
    overall = max((t["state"] for t in triggers.values()), key=lambda s: WORST_ORDER.get(s, 0))
    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "triggers": triggers,
        "overall": overall,
    }
