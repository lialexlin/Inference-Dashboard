"""Fetch 1-year daily prices + fundamentals snapshot via yfinance.

Resilient: any ticker that fails gets a per-ticker error logged and the rest
continue. Output JSON keys are the source ticker symbols (e.g., "000660.KS").
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class PriceResult:
    prices: dict[str, dict] = field(default_factory=dict)
    fundamentals: dict[str, dict] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


def _safe_float(x) -> float | None:
    if x is None:
        return None
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def _pct_change(history: list[dict], window_days: int) -> float | None:
    if not history:
        return None
    today_close = history[-1]["close"]
    cutoff = datetime.fromisoformat(history[-1]["date"]) - timedelta(days=window_days)
    past = next((h for h in reversed(history) if datetime.fromisoformat(h["date"]) <= cutoff), None)
    if past is None or past["close"] in (0, None):
        return None
    return round((today_close - past["close"]) / past["close"] * 100, 2)


def _ytd_change(history: list[dict]) -> float | None:
    if not history:
        return None
    today_close = history[-1]["close"]
    today_dt = datetime.fromisoformat(history[-1]["date"])
    year_start = datetime(today_dt.year, 1, 1)
    first_of_year = next((h for h in history if datetime.fromisoformat(h["date"]) >= year_start), None)
    if first_of_year is None or first_of_year["close"] in (0, None):
        return None
    return round((today_close - first_of_year["close"]) / first_of_year["close"] * 100, 2)


def fetch(tickers: list[str]) -> PriceResult:
    import yfinance as yf

    result = PriceResult()
    for ticker in tickers:
        try:
            yt = yf.Ticker(ticker)
            hist = yt.history(period="1y", auto_adjust=True)
            if hist is None or hist.empty:
                result.errors[ticker] = "no history returned"
                continue

            history = [
                {"date": idx.strftime("%Y-%m-%d"), "close": round(float(row["Close"]), 4)}
                for idx, row in hist.iterrows()
                if row.get("Close") is not None and not math.isnan(float(row["Close"]))
            ]
            if not history:
                result.errors[ticker] = "history empty after filtering"
                continue

            info = {}
            try:
                info = yt.info or {}
            except Exception as e:
                log.debug("info fetch failed for %s: %s", ticker, e)

            currency = info.get("currency") or "USD"
            last_close = history[-1]["close"]
            result.prices[ticker] = {
                "currency": currency,
                "last_close": last_close,
                "last_date": history[-1]["date"],
                "change_1m": _pct_change(history, 30),
                "change_6m": _pct_change(history, 182),
                "change_ytd": _ytd_change(history),
                "history": history,
            }
            result.fundamentals[ticker] = {
                "market_cap": _safe_float(info.get("marketCap")),
                "pe_trailing": _safe_float(info.get("trailingPE")),
                "pe_forward": _safe_float(info.get("forwardPE")),
                "revenue_growth": _safe_float(info.get("revenueGrowth")),
                "profit_margin": _safe_float(info.get("profitMargins")),
                "free_cashflow": _safe_float(info.get("freeCashflow")),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "long_name": info.get("longName") or info.get("shortName"),
                "currency": currency,
            }
            log.info("OK %s last=%s 1m=%s YTD=%s", ticker, last_close, result.prices[ticker]["change_1m"], result.prices[ticker]["change_ytd"])
        except Exception as e:
            log.warning("FAIL %s: %s", ticker, e)
            result.errors[ticker] = str(e)
    return result
