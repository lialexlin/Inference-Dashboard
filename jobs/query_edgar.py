#!/usr/bin/env python3
"""
Query EDGAR for all 47 tickers and identify new filings not in filing_summaries.json.
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

CIK_MAP = {
    "MU": "0000723125", "TSM": "0001046179", "INTC": "0000050863",
    "GFS": "0001709048", "AMKR": "0001047127", "ASML": "0000937966",
    "AMAT": "0000006951", "LRCX": "0000707549", "KLAC": "0000319201",
    "NVDA": "0001045810", "AMD": "0000002488", "AVGO": "0001730168",
    "MRVL": "0001835632", "GOOGL": "0001652044", "LITE": "0001633978",
    "COHR": "0000820318", "FN": "0001408710", "MXL": "0001288469",
    "ANET": "0001596532", "CSCO": "0000858877", "HPE": "0001645590",
    "CLS": "0001030894", "GEV": "0001996810", "ETN": "0001551182",
    "VRT": "0001674101", "GNRC": "0001437749", "CMI": "0000026172",
    "HUBB": "0000048898", "PWR": "0001050915", "CAT": "0000018230",
    "NVT": "0001720635", "MOD": "0000067347", "MSFT": "0000789019",
    "META": "0001326801", "AMZN": "0001018724", "ORCL": "0001341439",
    "CRWV": "0001769628", "NBIS": "0001513845", "CRM": "0001108524",
    "NOW": "0001373715", "SNOW": "0001640147", "PLTR": "0001321655",
    "CDNS": "0000813672", "SNPS": "0000883241", "CEG": "0001868275",
    "OKLO": "0001849056", "LEU": "0001065059",
}

HEADERS = {"User-Agent": "InferenceDashboard/0.1 (xelailnil@gmail.com)"}
TODAY = datetime(2026, 5, 15)
CUTOFF_DATE = TODAY - timedelta(days=365)


def fetch_url(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise e


def get_filings_for_ticker(ticker, cik):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        data = fetch_url(url)
    except Exception as e:
        print(f"  ERROR fetching {ticker}: {e}")
        return []

    filings = data.get("filings", {}).get("recent", {})
    if not filings:
        return []

    forms = filings.get("form", [])
    filed_dates = filings.get("filingDate", [])
    accession_nos = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])
    items_list = filings.get("items", [])

    results = []
    # Collect 10-K and 10-Q first (most recent 2 within 365 days)
    quarterly_annual = []
    earnings_8k_dates = []

    for i in range(len(forms)):
        form = forms[i]
        filed_str = filed_dates[i] if i < len(filed_dates) else ""
        if not filed_str:
            continue
        try:
            filed_dt = datetime.strptime(filed_str, "%Y-%m-%d")
        except ValueError:
            continue

        if filed_dt < CUTOFF_DATE:
            continue

        accession = accession_nos[i] if i < len(accession_nos) else ""
        primary_doc = primary_docs[i] if i < len(primary_docs) else ""

        if form in ("10-K", "10-Q"):
            quarterly_annual.append({
                "ticker": ticker,
                "cik": cik,
                "accession": accession,
                "form": form,
                "filed_date": filed_str,
                "primary_doc": primary_doc,
            })
        elif form == "8-K":
            items_str = items_list[i] if i < len(items_list) else ""
            if "2.02" in str(items_str):
                results.append({
                    "ticker": ticker,
                    "cik": cik,
                    "accession": accession,
                    "form": "8-K",
                    "filed_date": filed_str,
                    "primary_doc": primary_doc,
                    "items": items_str,
                })

    # Keep 2 most recent 10-K/10-Q
    quarterly_annual.sort(key=lambda x: x["filed_date"], reverse=True)
    results.extend(quarterly_annual[:2])

    return results


def main():
    # Load existing accessions
    with open("/home/user/Inference-Dashboard/data/filing_summaries.json") as f:
        existing = json.load(f)

    # Normalize accession format: remove dashes
    existing_accessions = set()
    for acc_key in existing.keys():
        existing_accessions.add(acc_key)
        existing_accessions.add(acc_key.replace("-", ""))

    print(f"Existing entries: {len(existing)}")
    print(f"Starting EDGAR queries for {len(CIK_MAP)} tickers...\n")

    all_new = []
    all_found = []

    for ticker, cik in CIK_MAP.items():
        print(f"Querying {ticker} (CIK {cik})...")
        filings = get_filings_for_ticker(ticker, cik)

        for f in filings:
            acc = f["accession"]
            acc_clean = acc.replace("-", "")
            all_found.append({"ticker": ticker, "accession": acc, "form": f["form"], "filed_date": f["filed_date"]})

            if acc not in existing_accessions and acc_clean not in existing_accessions:
                # Also check formatted version
                acc_fmt = f"{acc_clean[:10]}-{acc_clean[10:12]}-{acc_clean[12:]}"
                if acc_fmt not in existing_accessions:
                    all_new.append(f)
                    print(f"  NEW: {acc} ({f['form']} {f['filed_date']})")
            else:
                print(f"  EXISTS: {acc} ({f['form']} {f['filed_date']})")

        time.sleep(0.15)  # EDGAR rate limit

    print(f"\n{'='*60}")
    print(f"Total filings found: {len(all_found)}")
    print(f"NEW filings to process: {len(all_new)}")
    for n in all_new:
        print(f"  {n['ticker']} {n['form']} {n['filed_date']} {n['accession']}")

    # Save new filings list for further processing
    with open("/tmp/new_filings.json", "w") as f:
        json.dump(all_new, f, indent=2)

    print("\nSaved new filings to /tmp/new_filings.json")


if __name__ == "__main__":
    main()
