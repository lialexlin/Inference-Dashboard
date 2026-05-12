"""Per-ticker Business x Valuation scoring.

Combines CIQ fundamentals, multiples history, prices, signals, and user-curated
manual estimates into two equal-weighted z-scores per ticker, plus a quadrant
label. Layer status is rolled up from player quadrants.

Components are z-scored within each ticker's primary-layer peer set so the
comparison is apples-to-apples. Missing components are skipped, not penalized.

Sign convention: positive = "good" (strong growth or cheap valuation).
"""
from __future__ import annotations

import math
import re
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

# Quadrant decision thresholds. Tune after observing the first run.
THRESH = 0.3

# Layer-rollup thresholds.
ROLL_UNDER_FRACTION = 0.30
ROLL_PRICED_FRACTION = 0.50

# Signal-density window.
SIGNAL_DAYS = 90

OPS_TIGHTNESS_RE = re.compile(
    r"capex|lead.?time|shortage|constrain|backlog|sold.?out|allocate|gigawatt|\bGW\b|\bMW\b",
    re.IGNORECASE,
)


def _signal_text(s: dict) -> str:
    parts = [s.get("headline", "") or "", s.get("quote", "") or "", s.get("summary", "") or ""]
    return " ".join(str(p) for p in parts)


def _z(values: list[float], v: float) -> float | None:
    """z-score v against the peer values. Robust to tiny n."""
    if v is None or not values:
        return None
    if len(values) < 2:
        return 0.0
    mean = statistics.mean(values)
    try:
        std = statistics.pstdev(values)
    except statistics.StatisticsError:
        return 0.0
    if std == 0:
        return 0.0
    return (v - mean) / std


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.median(values)


def _ratio_vs(value: float | None, baseline: float | None) -> float | None:
    """Return (value - baseline) / baseline. None-safe."""
    if value is None or baseline is None or baseline == 0:
        return None
    return (value - baseline) / baseline


def _clamp(v: float, lo: float = -3.0, hi: float = 3.0) -> float:
    return max(lo, min(hi, v))


def _components_business(
    ticker: str,
    fund: dict,
    manual: dict,
    signal_density: int,
    layer_values: dict[str, list[float]],
    layer_signal_density: list[int],
) -> dict:
    """Per-ticker business components, z-scored within the layer."""
    ciq = (fund.get(ticker, {}) or {}).get("ciq", {}) or {}
    m = manual.get(ticker, {}) or {}

    out: dict[str, float] = {}

    # 1. Revenue YoY growth
    rev_yoy = ciq.get("revenue_yoy")
    z = _z(layer_values["revenue_yoy"], rev_yoy)
    if z is not None:
        out["biz_revenue_yoy_z"] = _clamp(z)

    # 2. Acceleration: YoY minus 3y CAGR (positive = accelerating)
    cagr3 = ciq.get("revenue_cagr_3y")
    if rev_yoy is not None and cagr3 is not None:
        accel = rev_yoy - cagr3
        z = _z(layer_values["accel"], accel)
        if z is not None:
            out["biz_accel_z"] = _clamp(z)

    # 3. EBITDA margin
    ebitda_m = ciq.get("ebitda_margin")
    z = _z(layer_values["ebitda_margin"], ebitda_m)
    if z is not None:
        out["biz_margin_z"] = _clamp(z)

    # 4. EPS revision direction (manual)
    fwd_curr = m.get("fwd_eps_curr")
    history = m.get("fwd_eps_history") or []
    if fwd_curr is not None and history:
        prior = history[0].get("value")
        revision = _ratio_vs(fwd_curr, prior)
        # Revision z-scored against layer peers' revisions (sparse — fall back to absolute)
        if revision is not None:
            # Use absolute revision when peer sample is too small.
            peer_revisions = layer_values.get("revision", [])
            if len(peer_revisions) >= 2:
                z = _z(peer_revisions, revision)
            else:
                # Map absolute: +10% → ~+1z, +20% → ~+2z
                z = revision * 10.0
            if z is not None:
                out["biz_eps_revision_z"] = _clamp(z)

    # 5. Signal density (capex / lead-time mentions, last 90d)
    z = _z([float(x) for x in layer_signal_density], float(signal_density))
    if z is not None:
        out["biz_signal_density_z"] = _clamp(z)

    return out


def _components_valuation(
    ticker: str,
    fund: dict,
    manual: dict,
    history: dict,
    prices: dict,
    layer_values: dict[str, list[float]],
) -> dict:
    """Per-ticker valuation components, z-scored within the layer.
    Sign convention flipped so positive = cheap.
    """
    ciq = (fund.get(ticker, {}) or {}).get("ciq", {}) or {}
    f_top = fund.get(ticker, {}) or {}
    m = manual.get(ticker, {}) or {}

    out: dict[str, float] = {}

    # 1. Current trailing P/E vs own 5y/8y median
    pe_now = ciq.get("pe_trailing")
    hist = (history.get(ticker) or {}).get("pe") or []
    if pe_now and hist:
        own_med = _median([h["value"] for h in hist if h.get("value") and h["value"] > 0])
        diff = _ratio_vs(pe_now, own_med)  # positive = above own history (expensive)
        if diff is not None:
            # Map: +50% above median = -1z, -50% = +1z. Cap at ~2.
            out["val_vs_own_pe_z"] = _clamp(-diff * 2.0)

    # 2. Forward P/E vs manual 5y median (if user provided)
    pe_fwd = f_top.get("pe_forward")
    fwd_med = m.get("fwd_pe_5y_median")
    if pe_fwd and fwd_med:
        diff = _ratio_vs(pe_fwd, fwd_med)
        if diff is not None:
            out["val_vs_own_fwd_pe_z"] = _clamp(-diff * 2.0)

    # 3. Trailing P/E vs layer peer median
    pe_peers = layer_values.get("pe_trailing", [])
    if pe_now and pe_peers:
        peer_med = _median(pe_peers)
        diff = _ratio_vs(pe_now, peer_med)
        if diff is not None:
            out["val_vs_peer_pe_z"] = _clamp(-diff * 2.0)

    # 4. EV/EBITDA vs layer peer median
    ev = ciq.get("ev_ebitda")
    ev_peers = layer_values.get("ev_ebitda", [])
    if ev and ev_peers:
        peer_med = _median(ev_peers)
        diff = _ratio_vs(ev, peer_med)
        if diff is not None:
            out["val_vs_peer_ev_z"] = _clamp(-diff * 2.0)

    # 5. 1y price return vs layer peer median (already rallied = expensive)
    px = prices.get(ticker, {}) or {}
    chg_1y = px.get("change_1y")
    if chg_1y is None:
        # Approximate: derive from history if change_1y missing
        h = px.get("history") or []
        if len(h) >= 252 and h[0].get("close") and h[-1].get("close"):
            chg_1y = (h[-1]["close"] - h[0]["close"]) / h[0]["close"] * 100.0
    chg_peers = layer_values.get("change_1y", [])
    if chg_1y is not None and chg_peers:
        peer_med = _median(chg_peers)
        if peer_med is not None:
            diff = chg_1y - peer_med  # percentage points above peer median
            # Map: +100pp above peers → -1z; -100pp → +1z. Cap.
            out["val_price_run_z"] = _clamp(-diff / 100.0)

    return out


def _layer_values_for_layer(
    layer_id: str,
    players: list[dict],
    fund: dict,
    manual: dict,
    prices: dict,
    signal_density_by_ticker: dict[str, int],
) -> dict[str, list[float]]:
    """Build the peer-set vector for each metric within this layer."""
    tickers = [p["ticker"] for p in players if p.get("layer_id") == layer_id]

    out: dict[str, list[float]] = defaultdict(list)
    for t in tickers:
        ciq = (fund.get(t, {}) or {}).get("ciq", {}) or {}
        rev_yoy = ciq.get("revenue_yoy")
        cagr3 = ciq.get("revenue_cagr_3y")
        if rev_yoy is not None:
            out["revenue_yoy"].append(rev_yoy)
            if cagr3 is not None:
                out["accel"].append(rev_yoy - cagr3)
        if ciq.get("ebitda_margin") is not None:
            out["ebitda_margin"].append(ciq["ebitda_margin"])
        if ciq.get("pe_trailing") and ciq["pe_trailing"] > 0:
            out["pe_trailing"].append(ciq["pe_trailing"])
        if ciq.get("ev_ebitda") and ciq["ev_ebitda"] > 0:
            out["ev_ebitda"].append(ciq["ev_ebitda"])

        # 1y price change (manual: derive if missing)
        px = prices.get(t, {}) or {}
        chg = px.get("change_1y")
        if chg is None:
            h = px.get("history") or []
            if len(h) >= 252 and h[0].get("close") and h[-1].get("close"):
                chg = (h[-1]["close"] - h[0]["close"]) / h[0]["close"] * 100.0
        if chg is not None:
            out["change_1y"].append(chg)

        # EPS revisions (manual)
        m = manual.get(t, {}) or {}
        fwd = m.get("fwd_eps_curr")
        hist = m.get("fwd_eps_history") or []
        if fwd is not None and hist and hist[0].get("value"):
            rev = (fwd - hist[0]["value"]) / hist[0]["value"]
            out["revision"].append(rev)

    return dict(out)


def _signal_density(
    signals: list[dict],
    now: datetime,
) -> dict[str, int]:
    """Count operational-tightness mentions per ticker in last SIGNAL_DAYS days."""
    cutoff = now - timedelta(days=SIGNAL_DAYS)
    counts: dict[str, int] = defaultdict(int)
    for s in signals:
        date_str = s.get("date")
        if not date_str:
            continue
        try:
            d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if d < cutoff:
            continue
        if not OPS_TIGHTNESS_RE.search(_signal_text(s)):
            continue
        for t in s.get("tickers") or []:
            counts[t] += 1
    return dict(counts)


def _quadrant(business: float | None, valuation: float | None) -> str:
    if business is None or valuation is None:
        return "unscored"
    if business > THRESH and valuation > THRESH:
        return "underappreciated"
    if business > THRESH and valuation < -THRESH:
        return "priced-in"
    if business < -THRESH and valuation > THRESH:
        return "value-trap"
    if business < -THRESH and valuation < -THRESH:
        return "avoid"
    return "fair"


def _avg(values: list[float]) -> float | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def _layer_status_from_quadrants(quadrants: list[str]) -> str:
    """Roll quadrant distribution into a layer label.

    Uses the same vocabulary as per-ticker quadrants so the card-level badge
    and the table-level pills speak one language.
    """
    scored = [q for q in quadrants if q != "unscored"]
    n = len(scored)
    if n == 0:
        return "fair"
    c_under  = sum(1 for q in scored if q == "underappreciated")
    c_priced = sum(1 for q in scored if q == "priced-in")
    c_trap   = sum(1 for q in scored if q == "value-trap")
    c_avoid  = sum(1 for q in scored if q == "avoid")
    # Top-idea zone is the actionable case → lowest bar.
    if c_under / n >= ROLL_UNDER_FRACTION:
        return "underappreciated"
    # Directional flags need a clearer majority.
    if c_priced / n >= ROLL_PRICED_FRACTION:
        return "priced-in"
    if c_trap / n >= ROLL_PRICED_FRACTION:
        return "value-trap"
    if c_avoid / n >= ROLL_PRICED_FRACTION:
        return "avoid"
    return "fair"


def compute(
    *,
    layers: list[dict],
    players: list[dict],
    fundamentals: dict,
    prices: dict,
    history: dict,
    signals: list[dict],
    manual: dict,
    now: datetime | None = None,
) -> tuple[dict, dict]:
    """Compute per-ticker scores and per-layer auto-statuses.

    Returns (scores_map, layer_status_auto_map).
    """
    now = now or datetime.now(timezone.utc)
    signal_density_by_ticker = _signal_density(signals, now)

    layer_ids = [l["id"] for l in layers]
    layer_values_cache = {
        lid: _layer_values_for_layer(lid, players, fundamentals, manual, prices, signal_density_by_ticker)
        for lid in layer_ids
    }

    # Per-layer signal density vector (for z-scoring the per-ticker count)
    layer_signal_density = {
        lid: [signal_density_by_ticker.get(p["ticker"], 0) for p in players if p.get("layer_id") == lid]
        for lid in layer_ids
    }

    scores: dict[str, dict] = {}
    quadrants_by_layer: dict[str, list[str]] = defaultdict(list)

    for p in players:
        t = p["ticker"]
        lid = p.get("layer_id")
        if not lid:
            continue
        peer_values = layer_values_cache.get(lid, {})

        biz_comps = _components_business(
            t, fundamentals, manual,
            signal_density_by_ticker.get(t, 0),
            peer_values,
            layer_signal_density.get(lid, []),
        )
        val_comps = _components_valuation(
            t, fundamentals, manual, history, prices, peer_values,
        )

        business = _avg(list(biz_comps.values()))
        valuation = _avg(list(val_comps.values()))
        q = _quadrant(business, valuation)
        quadrants_by_layer[lid].append(q)

        scores[t] = {
            "as_of": now.isoformat(),
            "business": None if business is None else round(business, 3),
            "valuation": None if valuation is None else round(valuation, 3),
            "quadrant": q,
            "components": {**{k: round(v, 3) for k, v in biz_comps.items()},
                           **{k: round(v, 3) for k, v in val_comps.items()}},
            "signal_density_90d": signal_density_by_ticker.get(t, 0),
        }

    # Layer auto-status
    layer_status_auto = {
        lid: _layer_status_from_quadrants(quadrants_by_layer.get(lid, []))
        for lid in layer_ids
    }

    return scores, layer_status_auto


def write_outputs(
    *,
    scores: dict,
    layer_status_auto: dict,
    fund_path,
    layers_path,
    scores_path,
    layers_data: list[dict],
    write_json,
) -> None:
    """Persist scores to scores.json, inject into fundamentals.json, and
    write status_auto into layers.json (preserving status / status_override).
    """
    import json
    # 1. scores.json (compact summary)
    summary = {
        t: {
            "business": s["business"],
            "valuation": s["valuation"],
            "quadrant": s["quadrant"],
            "signal_density_90d": s["signal_density_90d"],
        }
        for t, s in scores.items()
    }
    write_json(scores_path, summary)

    # 2. inject into fundamentals.json
    fund = json.loads(fund_path.read_text()) if fund_path.exists() else {}
    for t, s in scores.items():
        fund.setdefault(t, {})["score"] = s
    write_json(fund_path, fund)

    # 3. write status_auto into layers.json; preserve override
    new_layers = []
    for layer in layers_data:
        lid = layer["id"]
        auto = layer_status_auto.get(lid)
        override = layer.get("status_override")
        layer = dict(layer)
        layer["status_auto"] = auto
        # status (rendered) = override if set, else auto
        layer["status"] = override or auto or layer.get("status") or "fair"
        new_layers.append(layer)
    write_json(layers_path, new_layers)
