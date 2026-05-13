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


def _next_earnings(yt) -> dict[str, Any] | None:
    """Earliest upcoming earnings date from yfinance, with a `confirmed` flag.

    Reliability varies: solid for US large caps, spotty for ADRs and Asian
    listings — callers must render gracefully when None.
    """
    today = date.today()

    def _coerce(x) -> date | None:
        if x is None:
            return None
        if isinstance(x, date) and not isinstance(x, datetime):
            return x
        if isinstance(x, datetime):
            return x.date()
        try:
            return datetime.fromisoformat(str(x)[:10]).date()
        except (TypeError, ValueError):
            return None

    cal = None
    try:
        cal = yt.calendar
    except Exception:
        cal = None
    cal_dates: list[date] = []
    if isinstance(cal, dict):
        raw = cal.get("Earnings Date")
        if raw is not None:
            if isinstance(raw, (list, tuple)):
                cal_dates = [d for d in (_coerce(x) for x in raw) if d]
            else:
                d = _coerce(raw)
                if d:
                    cal_dates = [d]

    future_cal = sorted(d for d in cal_dates if d >= today)
    if future_cal:
        return {
            "date": future_cal[0].isoformat(),
            "range_end": future_cal[-1].isoformat() if len(future_cal) > 1 else None,
            "confirmed": len(cal_dates) == 1,
        }

    # Fallback: earnings_dates DataFrame includes both past and future.
    try:
        df = yt.earnings_dates
    except Exception:
        df = None
    if df is None or getattr(df, "empty", True):
        return None
    future: list[date] = []
    for idx in df.index:
        d = _coerce(idx)
        if d and d >= today:
            future.append(d)
    if not future:
        return None
    future.sort()
    return {"date": future[0].isoformat(), "range_end": None, "confirmed": False}


def _fx_to_usd(currency: str, cache: dict[str, float | None]) -> float | None:
    """Rate such that `usd_amount = local_amount / rate`. yfinance pair `USDxxx=X`
    quotes 1 USD in local currency. Returns None on failure (caller falls back)."""
    if not currency or currency == "USD":
        return 1.0
    if currency in cache:
        return cache[currency]
    import yfinance as yf

    try:
        h = yf.Ticker(f"USD{currency}=X").history(period="5d", auto_adjust=False)
        if h is None or h.empty:
            cache[currency] = None
            return None
        rate = float(h["Close"].iloc[-1])
        if math.isnan(rate) or rate <= 0:
            cache[currency] = None
            return None
        cache[currency] = rate
        log.info("FX USD/%s = %s", currency, rate)
        return rate
    except Exception as e:
        log.warning("FX fetch failed for USD/%s: %s", currency, e)
        cache[currency] = None
        return None


def fetch(tickers: list[str]) -> PriceResult:
    import yfinance as yf

    result = PriceResult()
    fx_cache: dict[str, float | None] = {}
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
            mcap_native = _safe_float(info.get("marketCap"))
            fx = _fx_to_usd(currency, fx_cache)
            mcap_usd = mcap_native / fx if (mcap_native is not None and fx) else None
            try:
                ne = _next_earnings(yt)
            except Exception as e:
                log.debug("next_earnings fetch failed for %s: %s", ticker, e)
                ne = None
            result.fundamentals[ticker] = {
                "market_cap": mcap_native,
                "market_cap_usd": mcap_usd,
                "pe_trailing": _safe_float(info.get("trailingPE")),
                "pe_forward": _safe_float(info.get("forwardPE")),
                "revenue_growth": _safe_float(info.get("revenueGrowth")),
                "profit_margin": _safe_float(info.get("profitMargins")),
                "free_cashflow": _safe_float(info.get("freeCashflow")),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "long_name": info.get("longName") or info.get("shortName"),
                "currency": currency,
                "next_earnings": ne,
            }
            log.info("OK %s last=%s 1m=%s YTD=%s", ticker, last_close, result.prices[ticker]["change_1m"], result.prices[ticker]["change_ytd"])
        except Exception as e:
            log.warning("FAIL %s: %s", ticker, e)
            result.errors[ticker] = str(e)
    return result
