"""Pull recent SEC filings (8-K / 10-Q / 10-K) for US-listed tickers via the
SEC EDGAR public submissions API. No key required.

We surface filings as signals — title + form + date + accession-number URL.
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
    "CMI": "0000026172",
    "HUBB": "0000048898",
    "PWR": "0001050915",
    "CAT": "0000018230",
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

INTERESTING_FORMS = {"8-K", "10-Q", "10-K"}


@dataclass
class EdgarResult:
    entries: list[dict] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


def _filing_url(cik: str, accession: str, primary_doc: str) -> str:
    acc_nodash = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{primary_doc}"


def fetch(tickers: list[str], days_back: int = 60, max_per_ticker: int = 5) -> EdgarResult:
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

            count = 0
            for i, form in enumerate(forms):
                if count >= max_per_ticker:
                    break
                if form not in INTERESTING_FORMS:
                    continue
                try:
                    fdate = datetime.fromisoformat(dates[i]).date()
                except Exception:
                    continue
                if fdate < cutoff:
                    continue
                desc = descriptions[i] if i < len(descriptions) else ""
                url_doc = _filing_url(cik, accessions[i], primary_docs[i])
                result.entries.append({
                    "id": f"edgar-{ticker}-{accessions[i]}",
                    "date": fdate.isoformat(),
                    "source": f"SEC EDGAR ({ticker})",
                    "source_type": "filing",
                    "headline": f"{ticker} files {form}: {desc or 'periodic report'}",
                    "quote": "",
                    "url": url_doc,
                    "layer_ids": [],
                    "tickers": [ticker],
                })
                count += 1
            log.info("OK EDGAR %s: %d filings", ticker, count)
            time.sleep(0.12)  # respect 10 req/sec cap
        except Exception as e:
            log.warning("FAIL EDGAR %s: %s", ticker, e)
            result.errors[ticker] = str(e)
    return result
