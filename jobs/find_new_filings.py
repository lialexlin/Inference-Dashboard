#!/usr/bin/env python3
"""
Query SEC EDGAR submissions API for all tickers and identify new filings
not yet in filing_summaries.json.
"""

import json
import time
import requests
from datetime import date, timedelta
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
HEADERS = {"User-Agent": "InferenceDashboard/0.1 (xelailnil@gmail.com)"}
CUTOFF_DATE = date(2025, 5, 19)   # filings must be on/after this date
TODAY = date(2026, 5, 19)

CIK_MAP = {
    "MU":    "0000723125", "TSM":   "0001046179", "INTC":  "0000050863",
    "GFS":   "0001709048", "AMKR":  "0001047127", "ASML":  "0000937966",
    "AMAT":  "0000006951", "LRCX":  "0000707549", "KLAC":  "0000319201",
    "NVDA":  "0001045810", "AMD":   "0000002488", "AVGO":  "0001730168",
    "MRVL":  "0001835632", "GOOGL": "0001652044", "LITE":  "0001633978",
    "COHR":  "0000820318", "FN":    "0001408710", "MXL":   "0001288469",
    "ANET":  "0001596532", "CSCO":  "0000858877", "HPE":   "0001645590",
    "CLS":   "0001030894", "GEV":   "0001996810", "ETN":   "0001551182",
    "VRT":   "0001674101", "GNRC":  "0001474735", "CMI":   "0000026172",
    "HUBB":  "0000048898", "PWR":   "0001050915", "CAT":   "0000018230",
    "NVT":   "0001720635", "MOD":   "0000067347", "MSFT":  "0000789019",
    "META":  "0001326801", "AMZN":  "0001018724", "ORCL":  "0001341439",
    "CRWV":  "0001769628", "NBIS":  "0001513845", "CRM":   "0001108524",
    "NOW":   "0001373715", "SNOW":  "0001640147", "PLTR":  "0001321655",
    "CDNS":  "0000813672", "SNPS":  "0000883241", "CEG":   "0001868275",
    "OKLO":  "0001849056", "LEU":   "0001065059",
}

# Existing accessions already in filing_summaries.json
EXISTING = {
    "0000002488-26-000018", "0000002488-26-000076", "0000018230-26-000008",
    "0000018230-26-000021", "0000026172-26-000009", "0000026172-26-000016",
    "0000050863-26-000011", "0000050863-26-000079", "0000319201-26-000008",
    "0000319201-26-000016", "0000707549-26-000009", "0000707549-26-000022",
    "0000723125-25-000044", "0000723125-25-000046", "0000723125-26-000004",
    "0000723125-26-000006", "0000813672-26-000016", "0000813672-26-000047",
    "0000820318-26-000006", "0000820318-26-000013", "0000858877-25-000171",
    "0000858877-26-000021", "0000883241-25-000028", "0000883241-26-000014",
    "0001018724-26-000004", "0001018724-26-000014", "0001030894-26-000011",
    "0001030894-26-000032", "0001045810-25-000230", "0001045810-26-000021",
    "0001047127-26-000014", "0001047127-26-000020", "0001050915-26-000006",
    "0001050915-26-000016", "0001104659-25-103646", "0001104659-26-010790",
    "0001108524-25-000238", "0001108524-26-000060", "0001193125-25-315925",
    "0001193125-26-027207", "0001193125-26-101045", "0001193125-26-191507",
    "0001288469-26-000011", "0001288469-26-000029", "0001321655-26-000011",
    "0001321655-26-000028", "0001373715-26-000007", "0001373715-26-000056",
    "0001408710-26-000008", "0001408710-26-000016", "0001437749-26-004568",
    "0001437749-26-014882", "0001551182-26-000007", "0001551182-26-000013",
    "0001596532-26-000013", "0001596532-26-000078", "0001628280-25-051349",
    "0001628280-25-056742", "0001628280-26-003942", "0001628280-26-005129",
    "0001628280-26-007117", "0001628280-26-007500", "0001628280-26-008608",
    "0001628280-26-009694", "0001628280-26-018698", "0001628280-26-026556",
    "0001628280-26-028526", "0001628280-26-029110", "0001628280-26-029370",
    "0001628280-26-030777", "0001628280-26-030891", "0001640147-25-000211",
    "0001640147-26-000008", "0001645590-25-000130", "0001645590-26-000032",
    "0001652044-26-000018", "0001652044-26-000048", "0001674101-26-000008",
    "0001730168-25-000121", "0001730168-26-000016", "0001769628-26-000104",
    "0001769628-26-000222", "0001835632-25-000197", "0001835632-26-000011",
    "0001868275-25-000092", "0001868275-26-000032", "0001996810-26-000015",
    "0001996810-26-000064",
}


def parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except Exception:
        return None


def fmt_accession(nodash):
    """Convert 0001045810-26-000021 style. Input may be either format."""
    nd = nodash.replace("-", "")
    return f"{nd[:10]}-{nd[10:12]}-{nd[12:]}"


def fetch_submissions(cik_str):
    """Fetch EDGAR submissions JSON for a given CIK (zero-padded 10-digit str)."""
    url = f"https://data.sec.gov/submissions/CIK{cik_str}.json"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def get_recent_filings(sub):
    """
    Returns a list of dicts from sub['filings']['recent'], one per filing row.
    EDGAR paginates older filings into sub['filings']['files']; we only need
    'recent' here (covers ~40 most recent filings, well past 365 days for most).
    If recent doesn't go back far enough for some tickers (e.g. MSFT/AMZN which
    file a lot), we also fetch the first continuation file.
    """
    recent = sub.get("filings", {}).get("recent", {})
    forms       = recent.get("form", [])
    dates       = recent.get("filingDate", [])
    accessions  = recent.get("accessionNumber", [])
    docs        = recent.get("primaryDocument", [])
    descs       = recent.get("primaryDocDescription", [])
    items_list  = recent.get("items", [])

    rows = []
    for i in range(len(forms)):
        rows.append({
            "form":        forms[i],
            "filed_date":  dates[i],
            "accession":   accessions[i],
            "primary_doc": docs[i] if i < len(docs) else "",
            "description": descs[i] if i < len(descs) else "",
            "items":       items_list[i] if i < len(items_list) else "",
        })
    return rows


def find_new_filings_for_ticker(ticker, cik_str):
    """
    Returns a list of new filing dicts for a given ticker.
    Logic:
      1. Find the 2 most recent 10-K or 10-Q filed on/after CUTOFF_DATE.
      2. Find any 8-K with items containing '2.02' filed within [-21, +1] days
         of one of those reports.
      3. Filter out any that already exist in EXISTING.
    """
    sub = fetch_submissions(cik_str)
    rows = get_recent_filings(sub)

    # Collect 10-K/10-Q within the window (most recent 2)
    annual_quarterly = []
    for row in rows:
        if row["form"] not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            continue
        fd = parse_date(row["filed_date"])
        if fd is None:
            continue
        if fd >= CUTOFF_DATE and fd <= TODAY:
            annual_quarterly.append((fd, row))

    # Sort by date descending, take 2 most recent
    annual_quarterly.sort(key=lambda x: x[0], reverse=True)
    aq_selected = annual_quarterly[:2]

    # Collect 8-Ks with item 2.02 within window of any selected report
    earnings_8ks = []
    aq_dates = [d for d, _ in aq_selected]

    for row in rows:
        if row["form"] not in ("8-K", "8-K/A"):
            continue
        items = row.get("items", "") or ""
        if "2.02" not in items:
            continue
        fd = parse_date(row["filed_date"])
        if fd is None:
            continue
        if fd < CUTOFF_DATE or fd > TODAY:
            continue
        # Check proximity to any of our selected 10-K/10-Q dates
        for aq_date in aq_dates:
            delta = (fd - aq_date).days
            if -21 <= delta <= 1:
                # Find the nearby report form
                nearby_form = None
                for d2, r2 in aq_selected:
                    if d2 == aq_date:
                        nearby_form = r2["form"]
                earnings_8ks.append((fd, row, nearby_form))
                break

    # Also include any 8-K item 2.02 within [-21, +1] of ANY 10-K/10-Q
    # in case we have more than 2 (for completeness in backfill mode)
    all_aq_dates = [d for d, _ in annual_quarterly]
    for row in rows:
        if row["form"] not in ("8-K", "8-K/A"):
            continue
        items = row.get("items", "") or ""
        if "2.02" not in items:
            continue
        fd = parse_date(row["filed_date"])
        if fd is None:
            continue
        if fd < CUTOFF_DATE or fd > TODAY:
            continue
        already = any(r[1]["accession"] == row["accession"] for r in earnings_8ks)
        if already:
            continue
        for aq_date in all_aq_dates:
            delta = (fd - aq_date).days
            if -21 <= delta <= 1:
                earnings_8ks.append((fd, row, "10-K/10-Q (outside top-2)"))
                break

    # Build result list
    candidates = []
    for fd, row, _ in aq_selected:
        candidates.append(row)
    for fd, row, nearby_form in earnings_8ks:
        row = dict(row)
        row["_nearby_form"] = nearby_form
        candidates.append(row)

    # Deduplicate and filter out existing
    seen = set()
    new_filings = []
    cik_int = int(cik_str)

    for row in candidates:
        acc_raw = row["accession"]
        # EDGAR returns accessions as "0001045810-26-000021" or "000104581026000021"
        # Normalise to dashed form
        acc_dashed = acc_raw if "-" in acc_raw else fmt_accession(acc_raw)
        acc_nodash = acc_dashed.replace("-", "")

        if acc_dashed in EXISTING:
            continue
        if acc_dashed in seen:
            continue
        seen.add(acc_dashed)

        new_filings.append({
            "ticker":          ticker,
            "cik":             cik_str,
            "cik_int":         cik_int,
            "form":            row["form"],
            "filed_date":      row["filed_date"],
            "accession":       acc_dashed,
            "accession_nodash": acc_nodash,
            "primary_doc":     row.get("primary_doc", ""),
            "description":     row.get("description", ""),
            "items":           row.get("items", ""),
            "nearby_form":     row.get("_nearby_form", ""),
        })

    return new_filings


def main():
    all_new = []
    errors = []

    for ticker, cik in CIK_MAP.items():
        try:
            new = find_new_filings_for_ticker(ticker, cik)
            if new:
                print(f"  {ticker}: {len(new)} new filing(s)")
                for f in new:
                    print(f"    [{f['form']}] {f['filed_date']} {f['accession']} items={f['items']!r}")
            else:
                print(f"  {ticker}: no new filings")
            all_new.extend(new)
        except Exception as e:
            print(f"  {ticker}: ERROR — {e}")
            errors.append((ticker, str(e)))
        time.sleep(0.15)

    print(f"\n{'='*60}")
    print(f"Total new filings found: {len(all_new)}")
    if errors:
        print(f"Errors ({len(errors)}): {errors}")

    # Write output JSON
    out_path = Path("/home/user/Inference-Dashboard/data/new_filings_found.json")
    with open(out_path, "w") as f:
        json.dump(all_new, f, indent=2)
    print(f"\nOutput written to: {out_path}")

    # Also print as JSON to stdout for capture
    print("\n=== JSON OUTPUT ===")
    print(json.dumps(all_new, indent=2))


if __name__ == "__main__":
    main()
