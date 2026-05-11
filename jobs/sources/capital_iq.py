"""Fetch trailing multiples + fundamentals + history from S&P Capital IQ via Snowflake.

Three batched queries (one round-trip each, scaled by `WHERE companyId IN (...)`):
    1. Snapshot multiples — Last Close family on the latest fiscal year.
    2. LTM fundamentals, margins, growth, returns.
    3. Eight-year annual history — Period Last multiples + raw TEV/EBITDA for
       deriving historical EV/EBITDA (Period Last EV/EBITDA isn't a CIQ field;
       we compute TEV(100018) / EBITDA(4051) per fiscal year).

Output JSON keys are dashboard ticker symbols (e.g., "000660.KS"). Tickers
without a `companyId` in the mapping are silently skipped.

Schema reference: ../Exponential-Growth/.claude/skills/s&p/SKILL.md
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class CIQResult:
    snapshot: dict[str, dict] = field(default_factory=dict)
    history: dict[str, dict] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


# Country-of-incorporation → reporting currency. The Inference-Dashboard
# tracks ADRs (TSM, ASML, etc.) whose home-country reporting currency differs
# from where they trade, so the suffix-of-ticker shortcut is unreliable. CIQ
# also doesn't expose a reporting-currency column directly (per SKILL.md), so
# refresh.py builds this map from the PLAYERS roster's `country` field and
# passes it in.
COUNTRY_TO_CURRENCY = {
    "US": "USD",
    "TW": "TWD",
    "KR": "KRW",
    "JP": "JPY",
    "CN": "CNY",
    "HK": "HKD",
    "NL": "EUR",
    "DE": "EUR",
    "FR": "EUR",
    "IE": "EUR",
    "AT": "EUR",
    "GB": "GBP",
    "CH": "CHF",
    "CA": "CAD",
    "SG": "SGD",
}


def get_connection():
    """Open a Snowflake connection using SF_* env vars from .env."""
    import snowflake.connector
    from dotenv import load_dotenv

    load_dotenv(Path.cwd() / ".env")
    return snowflake.connector.connect(
        account=os.environ["SF_ACCOUNT"],
        user=os.environ["SF_USER"],
        password=os.environ["SF_PASS"],
        database="MI_XPRESSCLOUD",
        schema="XPRESSFEED",
        warehouse="XF_READER_AXIOMASIA_WH",
        login_timeout=60,
    )


# Data-item IDs verified in SKILL.md against GDS / NVIDIA.
SNAPSHOT_ITEMS = {
    100066: "pe_trailing",       # Last Close P/E
    100063: "ev_ebitda",         # Last Close TEV/EBITDA
    100061: "ev_revenue",        # Last Close TEV/Total Revenue
    100064: "p_s",               # Last Close Market Cap/Revenue
    100067: "p_b",               # Last Close P/Book
    100052: "last_close_price",  # local currency
    100054: "market_cap_local",  # local currency
    100060: "tev_local",         # local currency
}

# LTM (periodTypeId = 4) — margins, growth, returns, raw fundamentals.
# Margins & growth & returns are stored in CIQ as percent (e.g. 61.7);
# we divide by 100 to match yfinance's fraction convention (0.617).
LTM_ITEMS = {
    28:    ("revenue_ltm", "scale"),         # local currency, in millions or units
    4051:  ("ebitda_ltm", "scale"),
    15:    ("net_income_ltm", "scale"),
    41571: ("net_income_to_co_ltm", "scale"),
    4378:  ("net_income_normalized_ltm", "scale"),
    4047:  ("ebitda_margin", "pct"),
    4074:  ("gross_margin", "pct"),
    4053:  ("ebit_margin", "pct"),
    4094:  ("net_margin", "pct"),
    4436:  ("fcf_margin", "pct"),
    4194:  ("revenue_yoy", "pct"),
    4196:  ("ebitda_yoy", "pct"),
    4383:  ("eps_yoy", "pct"),
    4221:  ("revenue_cagr_3y", "pct"),
    4234:  ("revenue_cagr_5y", "pct"),
    4128:  ("roe", "pct"),
    4178:  ("roa", "pct"),
    43905: ("roic", "pct"),
}

# Annual history (periodTypeId = 1, fiscalYear >= start_year).
HISTORY_ITEMS = {
    100003: "pe",        # Period Last P/E
    100013: "p_b",       # Period Last P/Book
    100015: "p_s",       # Period Last Mcap/Revenue
    100018: "_tev",      # Period Last TEV — combined with 4051 to derive EV/EBITDA
    4051:   "_ebitda",   # raw EBITDA — combined with TEV
}


def _fx_rates(cur, currencies: set[str]) -> dict[str, float]:
    """Return {iso_code: local_per_USD} for the given currencies. USD = 1.0."""
    rates = {"USD": 1.0}
    needed = [c for c in currencies if c != "USD"]
    if not needed:
        return rates
    placeholders = ",".join(f"'{c}'" for c in needed)
    cur.execute(f"""
        SELECT cu.isoCode, er.priceClose
        FROM CIQCURRENCY cu
        JOIN CIQEXCHANGERATE er ON er.currencyId = cu.currencyId
        WHERE cu.isoCode IN ({placeholders})
          AND er.snapId = 8
          AND er.latestSnapFlag = 1
    """)
    for iso, rate in cur.fetchall():
        if rate and rate > 0:
            rates[iso] = float(rate)
    missing = [c for c in needed if c not in rates]
    if missing:
        log.warning("CIQ FX missing for: %s — values in those currencies stay local", missing)
    return rates


def _to_usd(local_value: float | None, currency: str, rates: dict[str, float]) -> float | None:
    if local_value is None:
        return None
    rate = rates.get(currency)
    if not rate:
        return None
    return local_value / rate


# CIQ stores raw-fundamental values (revenue, EBITDA, NI, market cap, TEV) in
# MILLIONS of local currency. The dashboard's existing fundamentals.json keeps
# market_cap_usd as raw dollars (e.g. NVDA = 5_230_436_024_320). Multiply by
# this scale to keep the contract.
CIQ_VALUE_SCALE = 1_000_000


def _scale(v: float | None) -> float | None:
    return v * CIQ_VALUE_SCALE if v is not None else None


def fetch(
    tickers: list[str],
    company_id_map: dict[str, int],
    currency_map: dict[str, str] | None = None,
) -> CIQResult:
    """Pull CIQ data for the given tickers. `company_id_map[ticker] -> companyId`.

    `currency_map[ticker]` is the company's reporting currency (ISO code).
    When omitted, USD is assumed — caller should always supply it for
    non-US holdings to get correct USD conversions.

    Tickers missing from the map (or mapped to None) are skipped — caller may
    log them as unmapped. Network/SQL errors are caught and recorded as
    per-ticker errors so a bad row never tanks the whole stage.
    """
    currency_map = currency_map or {}
    result = CIQResult()

    # Filter to tickers that have a resolved companyId.
    ticker_to_cid = {t: int(company_id_map[t]) for t in tickers
                     if company_id_map.get(t) is not None}
    if not ticker_to_cid:
        log.warning("CIQ: no resolved companyIds among %d tickers — skipping fetch", len(tickers))
        return result
    cid_to_ticker = {cid: t for t, cid in ticker_to_cid.items()}
    cid_list = ",".join(str(c) for c in ticker_to_cid.values())
    log.info("CIQ: fetching %d tickers (%d resolved)", len(tickers), len(ticker_to_cid))

    try:
        conn = get_connection()
    except Exception as e:
        log.error("CIQ connect failed: %s", e)
        result.errors["__connection__"] = str(e)
        return result

    try:
        cur = conn.cursor()
        try:
            # FX rates for all currencies in the cohort.
            currencies = {currency_map.get(t, "USD") for t in ticker_to_cid}
            fx = _fx_rates(cur, currencies)

            # Company names (one query, cheap).
            cur.execute(f"SELECT companyId, companyName FROM CIQCOMPANY WHERE companyId IN ({cid_list})")
            names = {int(r[0]): r[1] for r in cur.fetchall()}

            # ── Query 1: snapshot multiples (latest annual fiscal year per company) ──
            snap_ids = ",".join(str(i) for i in SNAPSHOT_ITEMS)
            cur.execute(f"""
                WITH latest AS (
                    SELECT companyId, MAX(fiscalYear) AS fy
                    FROM CIQFINPERIOD
                    WHERE companyId IN ({cid_list}) AND periodTypeId = 1
                    GROUP BY companyId
                )
                SELECT fp.companyId, fd.dataItemId, fd.dataItemValue, fp.fiscalYear
                FROM CIQFINANCIALDATA fd
                JOIN CIQFINPERIOD fp ON fd.financialPeriodId = fp.financialPeriodId
                JOIN latest l ON l.companyId = fp.companyId AND l.fy = fp.fiscalYear
                WHERE fp.periodTypeId = 1
                  AND fd.dataItemId IN ({snap_ids})
            """)
            snap_rows: dict[int, dict[str, Any]] = {cid: {} for cid in ticker_to_cid.values()}
            snap_fy: dict[int, int] = {}
            for cid, item_id, value, fy in cur.fetchall():
                cid = int(cid)
                snap_rows[cid][SNAPSHOT_ITEMS[int(item_id)]] = float(value) if value is not None else None
                snap_fy[cid] = int(fy)

            # ── Query 2: latest fiscal-year fundamentals + margins/growth/returns ──
            # We use periodTypeId=1 (Annual) instead of 4 (LTM) so values reconcile
            # 1:1 with the company's annual filing. MAX(financialPeriodId) is unreliable
            # for LTM (period ids aren't monotonic with calendar time); fiscal-year-max
            # is unambiguous and stable until the next 10-K is filed.
            ltm_ids = ",".join(str(i) for i in LTM_ITEMS)
            cur.execute(f"""
                WITH latest AS (
                    SELECT companyId, MAX(fiscalYear) AS fy
                    FROM CIQFINPERIOD
                    WHERE companyId IN ({cid_list}) AND periodTypeId = 1
                    GROUP BY companyId
                )
                SELECT fp.companyId, fd.dataItemId, fd.dataItemValue
                FROM CIQFINANCIALDATA fd
                JOIN CIQFINPERIOD fp ON fd.financialPeriodId = fp.financialPeriodId
                JOIN latest l ON l.companyId = fp.companyId AND l.fy = fp.fiscalYear
                WHERE fp.periodTypeId = 1
                  AND fd.dataItemId IN ({ltm_ids})
            """)
            ltm_rows: dict[int, dict[str, Any]] = {cid: {} for cid in ticker_to_cid.values()}
            for cid, item_id, value in cur.fetchall():
                cid = int(cid)
                key, kind = LTM_ITEMS[int(item_id)]
                v = float(value) if value is not None else None
                if kind == "pct" and v is not None:
                    v = v / 100.0
                ltm_rows[cid][key] = v

            # ── Query 3: 8-year annual history ──
            history_start_year = date.today().year - 7  # FY(start_year)..FY(today)
            hist_ids = ",".join(str(i) for i in HISTORY_ITEMS)
            cur.execute(f"""
                SELECT fp.companyId, fp.fiscalYear, fd.dataItemId, fd.dataItemValue
                FROM CIQFINANCIALDATA fd
                JOIN CIQFINPERIOD fp ON fd.financialPeriodId = fp.financialPeriodId
                WHERE fp.companyId IN ({cid_list})
                  AND fp.periodTypeId = 1
                  AND fp.fiscalYear >= {history_start_year}
                  AND fd.dataItemId IN ({hist_ids})
                ORDER BY fp.companyId, fp.fiscalYear
            """)
            # cid -> {fy -> {item_key -> value}}
            hist_raw: dict[int, dict[int, dict[str, float]]] = {}
            for cid, fy, item_id, value in cur.fetchall():
                cid, fy = int(cid), int(fy)
                if value is None:
                    continue
                hist_raw.setdefault(cid, {}).setdefault(fy, {})[HISTORY_ITEMS[int(item_id)]] = float(value)
        finally:
            cur.close()
    finally:
        conn.close()

    today_str = date.today().isoformat()

    for ticker, cid in ticker_to_cid.items():
        snap = snap_rows.get(cid, {})
        ltm = ltm_rows.get(cid, {})
        if not snap and not ltm:
            result.errors[ticker] = "no rows returned (companyId may be wrong)"
            continue

        currency = currency_map.get(ticker, "USD")
        fx_rate = fx.get(currency)

        block = {
            "company_id": cid,
            "company_name": names.get(cid),
            "as_of": today_str,
            "fiscal_year": snap_fy.get(cid),
            "reporting_currency": currency,
            "fx_rate_used": fx_rate,
            # Last-close multiples (current snapshot)
            "pe_trailing":   snap.get("pe_trailing"),
            "ev_ebitda":     snap.get("ev_ebitda"),
            "ev_revenue":    snap.get("ev_revenue"),
            "p_s":           snap.get("p_s"),
            "p_b":           snap.get("p_b"),
            # Margins (fractions, 0.617 = 61.7%)
            "ebitda_margin": ltm.get("ebitda_margin"),
            "gross_margin":  ltm.get("gross_margin"),
            "ebit_margin":   ltm.get("ebit_margin"),
            "net_margin":    ltm.get("net_margin"),
            "fcf_margin":    ltm.get("fcf_margin"),
            # Growth / CAGR (fractions)
            "revenue_yoy":   ltm.get("revenue_yoy"),
            "ebitda_yoy":    ltm.get("ebitda_yoy"),
            "eps_yoy":       ltm.get("eps_yoy"),
            "revenue_cagr_3y": ltm.get("revenue_cagr_3y"),
            "revenue_cagr_5y": ltm.get("revenue_cagr_5y"),
            # Returns (fractions)
            "roe":  ltm.get("roe"),
            "roa":  ltm.get("roa"),
            "roic": ltm.get("roic"),
            # Raw fundamentals — scaled to raw dollars (CIQ stores in millions).
            "revenue_ltm_local":           _scale(ltm.get("revenue_ltm")),
            "ebitda_ltm_local":            _scale(ltm.get("ebitda_ltm")),
            "net_income_ltm_local":        _scale(ltm.get("net_income_ltm")),
            "net_income_to_co_ltm_local":  _scale(ltm.get("net_income_to_co_ltm")),
            "net_income_normalized_local": _scale(ltm.get("net_income_normalized_ltm")),
            "revenue_ltm_usd":             _scale(_to_usd(ltm.get("revenue_ltm"), currency, fx)),
            "ebitda_ltm_usd":              _scale(_to_usd(ltm.get("ebitda_ltm"), currency, fx)),
            "net_income_ltm_usd":          _scale(_to_usd(ltm.get("net_income_ltm"), currency, fx)),
            # Market cap (local + USD) — adjunct to yfinance's; we keep both.
            "market_cap_local": _scale(snap.get("market_cap_local")),
            "market_cap_usd":   _scale(_to_usd(snap.get("market_cap_local"), currency, fx)),
            "tev_local":        _scale(snap.get("tev_local")),
            "tev_usd":          _scale(_to_usd(snap.get("tev_local"), currency, fx)),
        }
        result.snapshot[ticker] = block

        # History — flatten {fy -> {key -> v}} into per-metric arrays sorted by year.
        years = hist_raw.get(cid, {})
        if years:
            sorted_fys = sorted(years.keys())
            ts = {"pe": [], "p_b": [], "p_s": [], "ev_ebitda": []}
            for fy in sorted_fys:
                row = years[fy]
                if "pe" in row:
                    ts["pe"].append({"year": fy, "value": round(row["pe"], 2)})
                if "p_b" in row:
                    ts["p_b"].append({"year": fy, "value": round(row["p_b"], 2)})
                if "p_s" in row:
                    ts["p_s"].append({"year": fy, "value": round(row["p_s"], 2)})
                tev, ebitda = row.get("_tev"), row.get("_ebitda")
                if tev is not None and ebitda and ebitda > 0:
                    ts["ev_ebitda"].append({"year": fy, "value": round(tev / ebitda, 2)})
            result.history[ticker] = ts

        log.info("CIQ OK %s pe=%s ev/ebitda=%s rev_yoy=%s",
                 ticker, block["pe_trailing"], block["ev_ebitda"], block["revenue_yoy"])

    return result
