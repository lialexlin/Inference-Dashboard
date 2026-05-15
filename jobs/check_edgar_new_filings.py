#!/usr/bin/env python3
"""Check EDGAR for new filings not already in filing_summaries.json."""

import json
import time
import urllib.request
from datetime import datetime, timedelta

TODAY = datetime(2026, 5, 15)
LOOKBACK_DAYS = 365
LOOKBACK_DATE = TODAY - timedelta(days=LOOKBACK_DAYS)

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
    "GNRC": "0001437749",
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
    "CEG": "0001868275",
    "OKLO": "0001849056",
    "LEU": "0001065059",
}

HEADERS = {"User-Agent": "InferenceDashboard/0.1 (xelailnil@gmail.com)"}


def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def normalize_accession(acc):
    """Convert accession with or without dashes to standard form with dashes."""
    acc = acc.replace("-", "")
    return f"{acc[:10]}-{acc[10:12]}-{acc[12:]}"


def main():
    # Load existing summaries
    with open("/home/user/Inference-Dashboard/data/filing_summaries.json") as f:
        existing = json.load(f)

    existing_accessions = set(existing.keys())
    print(f"Existing summaries: {len(existing_accessions)}")

    new_filings = []

    for ticker, cik in CIK_MAP.items():
        cik_int = int(cik)
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        data = fetch_url(url)
        time.sleep(0.15)

        if not data:
            print(f"  {ticker}: FAILED to fetch")
            continue

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filed_dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        items_list = recent.get("items", [])

        # Track which 10-K/10-Q are new for this ticker (to check 8-K pairs)
        periodic_dates = []

        for i, form in enumerate(forms):
            filed_date_str = filed_dates[i]
            try:
                filed_date = datetime.strptime(filed_date_str, "%Y-%m-%d")
            except:
                continue

            if filed_date < LOOKBACK_DATE:
                continue

            acc_raw = accessions[i]
            acc_norm = normalize_accession(acc_raw)

            if form in ("10-K", "10-Q"):
                periodic_dates.append(filed_date)
                if acc_norm not in existing_accessions:
                    primary_doc = primary_docs[i] if i < len(primary_docs) else ""
                    new_filings.append({
                        "ticker": ticker,
                        "cik": cik,
                        "cik_int": cik_int,
                        "accession": acc_norm,
                        "form": form,
                        "filed_date": filed_date_str,
                        "primary_document": primary_doc,
                    })
                    print(f"  NEW: {ticker} {form} {filed_date_str} {acc_norm}")

            elif form == "8-K":
                items = items_list[i] if i < len(items_list) else ""
                if "2.02" in str(items):
                    # Check if it's within [-21, +1] days of a periodic filing
                    is_paired = False
                    for pd_date in periodic_dates:
                        delta = (filed_date - pd_date).days
                        if -21 <= delta <= 1:
                            is_paired = True
                            break
                    # Also check if within [-21, +1] of any recently filed 10-K/10-Q in the window
                    if not is_paired:
                        # Try against all 10-K/10-Q in the filings (lookahead within recent list)
                        for j, form2 in enumerate(forms):
                            if form2 in ("10-K", "10-Q"):
                                try:
                                    other_date = datetime.strptime(filed_dates[j], "%Y-%m-%d")
                                except:
                                    continue
                                if other_date >= LOOKBACK_DATE:
                                    delta = (filed_date - other_date).days
                                    if -21 <= delta <= 1:
                                        is_paired = True
                                        break

                    if is_paired and acc_norm not in existing_accessions:
                        primary_doc = primary_docs[i] if i < len(primary_docs) else ""
                        new_filings.append({
                            "ticker": ticker,
                            "cik": cik,
                            "cik_int": cik_int,
                            "accession": acc_norm,
                            "form": "8-K",
                            "filed_date": filed_date_str,
                            "primary_document": primary_doc,
                            "items": str(items),
                        })
                        print(f"  NEW 8-K 2.02: {ticker} {filed_date_str} {acc_norm}")

        if not any(True for f in new_filings if f["ticker"] == ticker):
            pass  # Already handled above

    print(f"\nTotal new filings found: {len(new_filings)}")
    with open("/tmp/new_filings.json", "w") as f:
        json.dump(new_filings, f, indent=2)
    print("Written to /tmp/new_filings.json")


if __name__ == "__main__":
    main()
