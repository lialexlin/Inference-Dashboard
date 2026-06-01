"""Pull recent SEC filings (10-K / 10-Q + paired earnings 8-K) for US-listed
tickers via the SEC EDGAR public submissions API. No key required.

Scope is intentionally narrow:
  - 10-K (annual) and 10-Q (quarterly) reports
  - 8-K filings ONLY when their items list contains "2.02" (Results of
    Operations and Financial Condition — i.e., the earnings press release)
    AND they're filed within [-21, +1] days of a 10-Q/10-K we already kept.
    The asymmetric window covers fiscal-year-end pairs where the earnings
    8-K is released 1-3 weeks before the matching 10-K.
  - All other 8-Ks (5.02 exec changes, 8.01 other, etc.) are dropped.

The paired-8-K rule exists because forward guidance lives in the earnings
press release exhibit (ex-99.1) attached to the 8-K, not in the 10-Q/10-K
itself.

EDGAR enforces a 10 req/sec global cap and requires a User-Agent with contact.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)

# Set via env if you fork this — EDGAR requires a contact email.
USER_AGENT = "InferenceDashboard/0.1 (xelailnil@gmail.com)"

# Ticker → CIK (zero-padded 10 digits). Maintained list, US-listed only.
CIK_MAP = {
    "MU": "0000723125",
    "TSM": "0001046179",
    "INTC": "0000050863",
    "GFS": "0001709048",
    "AMKR": "0001047127",
    "ASML": "0000937966",
    "AMAT": "0000006951",
    "LRCX": "0000707549",
    "KLAC": "0000319201",
    "NVDA": "0001045810",
    "AMD": "0000002488",
    "AVGO": "0001730168",
    "MRVL": "0001835632",
    "GOOGL": "0001652044",
    "LITE": "0001633978",
    "COHR": "0000820318",
    "FN": "0001408710",
    "MXL": "0001288469",
    "ANET": "0001596532",
    "CSCO": "0000858877",
    "HPE": "0001645590",
    "CLS": "0001030894",
    "GEV": "0001996810",
    "ETN": "0001551182",
    "VRT": "0001674101",
    "GNRC": "0001474735",
    "HUBB": "0000048898",
    "PWR": "0001050915",
    "NVT": "0001720635",
    "MOD": "0000067347",
    "MSFT": "0000789019",
    "META": "0001326801",
    "AMZN": "0001018724",
    "ORCL": "0001341439",
    "CRWV": "0001769628",
    "NBIS": "0001513845",
    "CRM": "0001108524",
    "NOW": "0001373715",
    "SNOW": "0001640147",
    "PLTR": "0001321655",
    "CDNS": "0000813672",
    "SNPS": "0000883241",
    "CEG":  "0001868275",
    "OKLO": "0001849056",
    "LEU":  "0001065059",
}

REPORT_FORMS = {"10-K", "10-Q"}
EARNINGS_8K_ITEM = "2.02"  # SEC item code for "Results of Operations and Financial Condition"


@dataclass
class EdgarResult:
    entries: list[dict] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


def _filing_url(cik: str, accession: str, primary_doc: str) -> str:
    acc_nodash = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{primary_doc}"


def _make_entry(ticker: str, cik: str, form: str, fdate, accession: str,
                primary_doc: str, desc: str) -> dict:
    # EDGAR sometimes returns the form name as the description (e.g. "8-K"),
    # which would produce headlines like "MU files 8-K: 8-K". Treat that as
    # empty so the form-specific fallback takes over.
    if desc and desc.strip().upper() == form.upper():
        desc = ""
    if not desc:
        desc = "Earnings release" if form == "8-K" else "periodic report"
    return {
        "id": f"edgar-{ticker}-{accession}",
        "accession": accession,
        "form": form,
        "date": fdate.isoformat(),
        "source": f"SEC EDGAR ({ticker})",
        "source_type": "filing",
        "headline": f"{ticker} files {form}: {desc}",
        "quote": "",
        "url": _filing_url(cik, accession, primary_doc),
        "layer_ids": [],
        "tickers": [ticker],
    }


def fetch(tickers: list[str], days_back: int = 365, max_reports_per_ticker: int = 2) -> EdgarResult:
    """Fetch the last `max_reports_per_ticker` 10-K/10-Q per ticker, plus any
    8-K with Item 2.02 (earnings release) filed within [-21, +1] days of one
    of those reports. days_back of 365 comfortably catches 4 quarterly
    reports."""
    import requests

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).date()
    result = EdgarResult()

    for ticker in tickers:
        cik = CIK_MAP.get(ticker)
        if not cik:
            continue
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            accessions = recent.get("accessionNumber", [])
            primary_docs = recent.get("primaryDocument", [])
            descriptions = recent.get("primaryDocDescription", [])
            items_list = recent.get("items", [])

            # Pass 1: collect the most recent 10-K/10-Q reports.
            reports: list[dict] = []
            report_dates: list = []
            for i, form in enumerate(forms):
                if form not in REPORT_FORMS:
                    continue
                try:
                    fdate = datetime.fromisoformat(dates[i]).date()
                except Exception:
                    continue
                if fdate < cutoff:
                    continue
                if len(reports) >= max_reports_per_ticker:
                    break
                desc = descriptions[i] if i < len(descriptions) else ""
                reports.append(_make_entry(ticker, cik, form, fdate, accessions[i], primary_docs[i], desc))
                report_dates.append(fdate)

            # Pass 2: collect 8-Ks with item 2.02 filed within ±1 day of a kept report.
            earnings_8ks: list[dict] = []
            for i, form in enumerate(forms):
                if form != "8-K":
                    continue
                items = items_list[i] if i < len(items_list) else ""
                if EARNINGS_8K_ITEM not in (items or ""):
                    continue
                try:
                    fdate = datetime.fromisoformat(dates[i]).date()
                except Exception:
                    continue
                # Earnings 8-K is released BEFORE the matching periodic report
                # (1 day before for 10-Qs, often 1-3 weeks before for 10-Ks).
                # A symmetric ±1 day window misses every fiscal-year-end pair.
                if not any(-21 <= (fdate - rd).days <= 1 for rd in report_dates):
                    continue
                desc = descriptions[i] if i < len(descriptions) else ""
                earnings_8ks.append(_make_entry(ticker, cik, form, fdate, accessions[i], primary_docs[i], desc or "Earnings release"))

            result.entries.extend(reports)
            result.entries.extend(earnings_8ks)
            log.info("OK EDGAR %s: %d reports + %d earnings 8-Ks",
                     ticker, len(reports), len(earnings_8ks))
            time.sleep(0.12)  # respect 10 req/sec cap
        except Exception as e:
            log.warning("FAIL EDGAR %s: %s", ticker, e)
            result.errors[ticker] = str(e)
    return result
