"""Compute per-layer tightness scores from signal density + supply-language extraction.

A "tightness" score (0-100) summarizes how *binding* each layer is right now —
this is the dashboard's view of which layer the market is rotating toward.

Inputs (passed in by refresh.py):
  - layers:  list of layer dicts (from layers.json)
  - signals: list of signal dicts (already tagged with layer_ids + arch_risk)
  - cross_quarter: dict (ticker -> {shifts, verdict, ...}) from data/cross_quarter.json
  - players: list of player dicts (used to map ticker -> primary layer)

Output:
  - dict {layer_id: {tightness_score, evidence: [up-to-3 quotes], updated_at,
                     components: {density_pct, language_density, supply_signal_pct}}}

Scoring (0-100 composite, weights documented inline):
  - 40% signal_density_90d, percentile-ranked across layers
  - 40% tightness_language_density (hits per signal of supply-tightness terms)
  - 20% cross_quarter_supply_signal (binary +20 if any ticker in layer has
        a recent cross-quarter "shift" with area=supply, direction=tight)
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

# Supply-tightness language. These hits mean "demand exceeds supply" — the
# textual fingerprint of a binding bottleneck.
TIGHTNESS_TERMS: list[str] = [
    "allocated",
    "allocation",
    "sold out",
    "sold-out",
    "lead time",
    "lead-time",
    "supply constrained",
    "supply-constrained",
    "constrained",
    "tight",
    "shortage",
    "backlog",
    "book-to-bill",
    "book to bill",
    "capacity-limited",
    "capacity limited",
    "cannot meet demand",
    "outstripping supply",
    "demand outpaces supply",
    "demand exceeds supply",
    "ramp constraint",
    "supply gap",
]

WINDOW_DAYS = 90


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower())


def _tightness_hits(text: str) -> int:
    return sum(1 for term in TIGHTNESS_TERMS if term in text)


def _percentile_rank(values: list[float], v: float) -> float:
    """Return percentile of v inside values (0-1 scale)."""
    if not values:
        return 0.0
    below = sum(1 for x in values if x < v)
    return below / len(values)


def compute(
    layers: list[dict],
    signals: list[dict],
    cross_quarter: dict[str, dict],
    players: list[dict],
) -> dict[str, dict]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=WINDOW_DAYS)

    # Index ticker -> primary layer for cross-quarter rollup
    ticker_to_layer = {p["ticker"]: p["layer_id"] for p in players}

    # Bucket signals per layer (within window)
    per_layer_sigs: dict[str, list[dict]] = {l["id"]: [] for l in layers}
    for s in signals:
        try:
            sig_date = datetime.fromisoformat(s["date"]).replace(tzinfo=timezone.utc)
        except Exception:
            try:
                sig_date = datetime.fromisoformat(s["date"] + "T00:00:00+00:00")
            except Exception:
                continue
        if sig_date < cutoff:
            continue
        for lid in s.get("layer_ids") or []:
            if lid in per_layer_sigs:
                per_layer_sigs[lid].append(s)

    # Cross-quarter supply-tight rollup per layer
    cq_supply_per_layer: dict[str, list[str]] = {l["id"]: [] for l in layers}
    for ticker, cq in cross_quarter.items():
        layer = ticker_to_layer.get(ticker)
        if not layer or layer not in cq_supply_per_layer:
            continue
        for shift in cq.get("shifts") or []:
            if (shift.get("area") or "").lower() == "supply" and (shift.get("direction") or "").lower() == "tight":
                note = shift.get("trend") or shift.get("note") or ""
                cq_supply_per_layer[layer].append(f"[{ticker}] {note}")

    # Raw density per layer, plus tightness-language hits per signal
    raw_density: dict[str, int] = {}
    lang_density: dict[str, float] = {}
    evidence_pool: dict[str, list[tuple[int, str]]] = {l["id"]: [] for l in layers}
    for lid, sigs in per_layer_sigs.items():
        raw_density[lid] = len(sigs)
        if not sigs:
            lang_density[lid] = 0.0
            continue
        total_hits = 0
        for s in sigs:
            text = _norm(f"{s.get('headline', '')} {s.get('quote', '')}")
            hits = _tightness_hits(text)
            total_hits += hits
            if hits > 0:
                quote = s.get("quote") or s.get("headline") or ""
                evidence_pool[lid].append((hits, quote[:240]))
        lang_density[lid] = total_hits / max(1, len(sigs))

    # Percentile-rank density and language across layers
    density_values = list(raw_density.values())
    lang_values = list(lang_density.values())

    out: dict[str, dict] = {}
    for layer in layers:
        lid = layer["id"]
        d_pct = _percentile_rank(density_values, raw_density.get(lid, 0))
        l_pct = _percentile_rank(lang_values, lang_density.get(lid, 0.0))
        cq_supply_evidence = cq_supply_per_layer.get(lid, [])
        cq_score = 1.0 if cq_supply_evidence else 0.0

        score = round(100 * (0.4 * d_pct + 0.4 * l_pct + 0.2 * cq_score))

        # Top-3 evidence: sort by hit count desc, dedupe by leading 80 chars
        seen: set[str] = set()
        dedup: list[str] = []
        for _, q in sorted(evidence_pool[lid], key=lambda t: -t[0]):
            key = q[:80]
            if key in seen:
                continue
            seen.add(key)
            dedup.append(q)
            if len(dedup) >= 3:
                break
        # Backfill with cross-quarter evidence if we're short
        if len(dedup) < 3:
            for cq_note in cq_supply_evidence[: 3 - len(dedup)]:
                dedup.append(cq_note)

        out[lid] = {
            "tightness_score": score,
            "signal_count_90d": raw_density.get(lid, 0),
            "tightness_language_hits_per_signal": round(lang_density.get(lid, 0.0), 3),
            "cross_quarter_supply_tight": bool(cq_supply_evidence),
            "evidence": dedup,
            "components": {
                "density_pct": round(d_pct, 3),
                "language_pct": round(l_pct, 3),
                "supply_signal": cq_score,
            },
            "updated_at": now.isoformat(),
        }

    return out
