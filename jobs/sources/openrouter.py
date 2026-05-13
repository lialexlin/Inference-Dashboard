"""OpenRouter demand telemetry — scrape /rankings for daily token throughput.

OpenRouter's rankings page server-renders a `rankingData` array containing
per-(model, day) totals: total_prompt_tokens, total_completion_tokens, count.
Each fetch returns 4 recent days. We accumulate snapshots into a rolling
history so the series grows with each daily refresh.

Schema of data/demand_signals.json:
{
  "as_of": "2026-05-13T...",
  "daily": [
    {
      "date": "2026-05-12",
      "total_tokens_b": 1234.5,
      "total_requests": 12345678,
      "top_models": [
        {"model": "google/gemini-3.1-flash-lite-...", "tokens_b": 123.4, "share": 0.099, "requests": 6789012},
        ...
      ]
    }, ...
  ],
  "summary": {
    "latest_total_tokens_b": ...,
    "wow_pct": ...,        # vs 7 days prior
    "dod_pct": ...,        # vs prior day
    "top_movers_wow": [    # top movers by week-over-week token-share change
      {"model": "...", "share_now": 0.142, "share_prev": 0.098, "share_delta": +0.044}, ...
    ]
  }
}

Graceful degradation: any HTTP or parse failure preserves the existing
demand_signals.json. The refresh stage records an error in meta.json.sources.openrouter.
"""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen

LOG = logging.getLogger(__name__)

URL = "https://openrouter.ai/rankings"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
TIMEOUT = 30
MAX_HISTORY_DAYS = 200          # cap rolling history at ~6 months
TOP_MODELS_PER_DAY = 10


def _fetch_html() -> str:
    req = Request(URL, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace")


def _extract_ranking_records(html: str) -> list[dict]:
    """Pull the rankingData entries from the RSC streamed payload.

    Pattern: self.__next_f.push([1,"<escaped-json-chunk>"]) — combine all chunks,
    then locate '"rankingData":[' and parse the array.
    """
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.S)
    combined = "".join(
        bytes(c, "utf-8").decode("unicode_escape", errors="ignore") for c in chunks
    )
    # Find every entry. The records are dicts with model_permaslug + date.
    # We pull them via a regex-anchored brace-match to survive the streamed format.
    records: list[dict] = []
    for m in re.finditer(r'\{"date":"(\d{4}-\d{2}-\d{2})[^"]*","model_permaslug":"([^"]+)"', combined):
        date, slug = m.group(1), m.group(2)
        # Walk forward to find the closing brace of this object.
        start = m.start()
        depth = 0
        end = -1
        for i in range(start, min(start + 4000, len(combined))):
            ch = combined[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end < 0:
            continue
        try:
            obj = json.loads(combined[start:end])
        except Exception:
            continue
        records.append(obj)
    return records


def _dominant_date(records: list[dict]) -> str | None:
    """Return the most-frequent date string in the record set.

    OpenRouter's rankings response is a snapshot: ~99% of records carry the
    same date (the snapshot date), with a handful of stale/edge records
    leaking in for other dates. We keep only the dominant date so the daily
    series isn't polluted with sparse outlier rows.
    """
    counts: dict[str, int] = defaultdict(int)
    for r in records:
        d = (r.get("date") or "")[:10]
        if d:
            counts[d] += 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]


def _aggregate_for_date(records: list[dict], date: str) -> dict:
    """Sum token totals + per-model breakdown for the given snapshot date.

    Numbers are cumulative-to-date as reported by OpenRouter; meaningful when
    compared across snapshots (DoD/WoW deltas).
    """
    agg = {"prompt": 0, "completion": 0, "reasoning": 0, "count": 0,
           "models": defaultdict(lambda: {"tokens": 0, "requests": 0})}
    for r in records:
        if (r.get("date") or "")[:10] != date:
            continue
        prompt = int(r.get("total_prompt_tokens", 0) or 0)
        completion = int(r.get("total_completion_tokens", 0) or 0)
        reasoning = int(r.get("total_native_tokens_reasoning", 0) or 0)
        count = int(r.get("count", 0) or 0)
        slug = r.get("model_permaslug", "")
        agg["prompt"] += prompt
        agg["completion"] += completion
        agg["reasoning"] += reasoning
        agg["count"] += count
        if slug:
            tokens = prompt + completion + reasoning
            m = agg["models"][slug]
            m["tokens"] += tokens
            m["requests"] += count
    return agg


def _shape_snapshot(date: str, agg: dict) -> dict:
    """Build a single snapshot row with totals + top_models[] for storage."""
    total_tokens = agg["prompt"] + agg["completion"] + agg["reasoning"]
    ranked = sorted(agg["models"].items(), key=lambda kv: -kv[1]["tokens"])
    top = []
    for slug, mv in ranked[:TOP_MODELS_PER_DAY]:
        share = mv["tokens"] / total_tokens if total_tokens else 0.0
        top.append({
            "model": slug,
            "tokens_b": round(mv["tokens"] / 1e9, 3),
            "share": round(share, 4),
            "requests": mv["requests"],
        })
    return {
        "date": date,
        "total_tokens_b": round(total_tokens / 1e9, 3),
        "total_prompt_tokens_b": round(agg["prompt"] / 1e9, 3),
        "total_completion_tokens_b": round(agg["completion"] / 1e9, 3),
        "total_reasoning_tokens_b": round(agg["reasoning"] / 1e9, 3),
        "total_requests": agg["count"],
        "top_models": top,
    }


def _merge_history(existing: list[dict], fresh: list[dict]) -> list[dict]:
    """Latest snapshot wins per date; cap at MAX_HISTORY_DAYS rows."""
    by_date = {e["date"]: e for e in existing}
    for row in fresh:
        by_date[row["date"]] = row
    merged = sorted(by_date.values(), key=lambda x: x["date"])
    return merged[-MAX_HISTORY_DAYS:]


def _summarize(daily: list[dict]) -> dict:
    """Compute DoD / WoW totals and top model-share movers."""
    if not daily:
        return {}
    latest = daily[-1]
    by_date = {d["date"]: d for d in daily}

    def pct(now: float, prev: float) -> float | None:
        if prev is None or prev <= 0 or now is None:
            return None
        return round((now - prev) / prev, 4)

    # DoD
    dod_prev = daily[-2] if len(daily) >= 2 else None
    # WoW: walk back 7 calendar days
    import datetime as _dt
    latest_dt = _dt.date.fromisoformat(latest["date"])
    target_str = (latest_dt - _dt.timedelta(days=7)).isoformat()
    wow_prev = by_date.get(target_str)

    out: dict[str, Any] = {
        "latest_date": latest["date"],
        "latest_total_tokens_b": latest["total_tokens_b"],
        "latest_total_requests": latest["total_requests"],
        "dod_pct": pct(latest["total_tokens_b"], dod_prev["total_tokens_b"]) if dod_prev else None,
        "wow_pct": pct(latest["total_tokens_b"], wow_prev["total_tokens_b"]) if wow_prev else None,
    }

    # Top movers: share-delta vs 7d ago
    if wow_prev:
        prev_shares = {m["model"]: m["share"] for m in wow_prev.get("top_models", [])}
        now_shares = {m["model"]: m["share"] for m in latest.get("top_models", [])}
        all_models = set(prev_shares) | set(now_shares)
        movers = []
        for slug in all_models:
            s_now = now_shares.get(slug, 0.0)
            s_prev = prev_shares.get(slug, 0.0)
            delta = s_now - s_prev
            movers.append({"model": slug, "share_now": round(s_now, 4),
                           "share_prev": round(s_prev, 4), "share_delta": round(delta, 4)})
        movers.sort(key=lambda x: -x["share_delta"])
        out["top_movers_wow"] = movers[:5]
        out["top_losers_wow"] = list(reversed(movers))[:5]

    return out


def fetch(existing: list[dict] | None = None) -> dict:
    """Fetch OpenRouter rankings, merge with existing daily history, summarize.

    `existing` is the prior `daily` array (from data/demand_signals.json).
    Returns a fresh demand_signals.json payload — caller is responsible for
    writing it (and recording per-stage meta).

    Raises on network or parse failure so caller can record the error and
    preserve prior state.
    """
    html = _fetch_html()
    records = _extract_ranking_records(html)
    if not records:
        raise RuntimeError("openrouter rankings: no ranking records parsed")
    snapshot_date = _dominant_date(records)
    if not snapshot_date:
        raise RuntimeError("openrouter rankings: no dominant date in records")
    agg = _aggregate_for_date(records, snapshot_date)
    fresh_row = _shape_snapshot(snapshot_date, agg)
    LOG.info("OpenRouter snapshot %s: %d records → %.1fB tokens across %d models",
             snapshot_date, len(records), fresh_row["total_tokens_b"], len(agg["models"]))

    merged = _merge_history(existing or [], [fresh_row])
    summary = _summarize(merged)

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source": "openrouter.ai/rankings",
        "daily": merged,
        "summary": summary,
    }
