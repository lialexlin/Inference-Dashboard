"""
One-shot EDGAR discovery script.
Queries SEC submissions API for each ticker, finds new 10-K/10-Q/8-K filings,
fetches MD&A or guidance text, writes filing_discovery.json.
"""

import json
import time
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests as _requests

SESSION = _requests.Session()
SESSION.headers.update({
    "User-Agent": "InferenceDashboard/0.1 (xelailnil@gmail.com)",
    "Accept": "application/json, text/html, */*",
    "Accept-Encoding": "gzip, deflate",
})

CUTOFF = "2025-05-17"
TODAY = "2026-05-17"
WAIT = 0.18  # 180ms between requests

CIK_MAP = {
    "MU": "0000723125", "TSM": "0001046179", "INTC": "0000050863",
    "GFS": "0001709048", "AMKR": "0001047127", "ASML": "0000937966",
    "AMAT": "0000006951", "LRCX": "0000707549", "KLAC": "0000319201",
    "NVDA": "0001045810", "AMD": "0000002488", "AVGO": "0001730168",
    "MRVL": "0001835632", "GOOGL": "0001652044", "LITE": "0001633978",
    "COHR": "0000820318", "FN": "0001408710", "MXL": "0001288469",
    "ANET": "0001596532", "CSCO": "0000858877", "HPE": "0001645590",
    "CLS": "0001030894", "GEV": "0001996810", "ETN": "0001551182",
    "VRT": "0001674101", "GNRC": "0001474735", "CMI": "0000026172",
    "HUBB": "0000048898", "PWR": "0001050915", "CAT": "0000018230",
    "NVT": "0001720635", "MOD": "0000067347", "MSFT": "0000789019",
    "META": "0001326801", "AMZN": "0001018724", "ORCL": "0001341439",
    "CRWV": "0001769628", "NBIS": "0001513845", "CRM": "0001108524",
    "NOW": "0001373715", "SNOW": "0001640147", "PLTR": "0001321655",
    "CDNS": "0000813672", "SNPS": "0000883241", "CEG": "0001868275",
    "OKLO": "0001849056", "LEU": "0001065059",
}

def fetch_url(url, binary=False):
    try:
        r = SESSION.get(url, timeout=30)
        r.raise_for_status()
        if binary:
            return r.content
        return r.text
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None

def load_covered_accessions():
    path = Path("data/filing_summaries.json")
    if not path.exists():
        return set(), {}
    with open(path) as f:
        data = json.load(f)
    # data is dict keyed by accession
    accessions = set(data.keys())
    # Also build last_covered_date per ticker
    ticker_last = {}
    for acc, v in data.items():
        t = v.get("ticker", "")
        d = v.get("filed_date", "")
        if t and d:
            if t not in ticker_last or d > ticker_last[t]:
                ticker_last[t] = d
    return accessions, ticker_last

def get_submissions(cik):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    time.sleep(WAIT)
    text = fetch_url(url)
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception as e:
        print(f"  ERROR parsing submissions JSON: {e}")
        return None

def find_eligible_filings(submissions, ticker, covered_accessions, ticker_last):
    """
    Find:
    - 2 most recent 10-K or 10-Q filed after CUTOFF (2025-05-17)
    - Any 8-K with item 2.02 filed within [-21, +1] days of those 10-K/10-Q dates
    Skip already covered accessions.
    Only return filings NOT already in covered_accessions.
    """
    recent = submissions.get("filings", {}).get("recent", {})
    if not recent:
        return []

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    items_list = recent.get("items", [])

    # Build full list of filings
    all_filings = []
    for i in range(len(forms)):
        acc = accessions[i] if i < len(accessions) else ""
        date = dates[i] if i < len(dates) else ""
        form = forms[i] if i < len(forms) else ""
        pdoc = primary_docs[i] if i < len(primary_docs) else ""
        items = items_list[i] if i < len(items_list) else ""
        all_filings.append({
            "form": form,
            "filed_date": date,
            "accession": acc,
            "primary_doc": pdoc,
            "items": items,
        })

    # Sort by date desc
    all_filings.sort(key=lambda x: x["filed_date"], reverse=True)

    # Find 2 most recent 10-K or 10-Q after cutoff
    anchor_filings = []
    anchor_dates = []
    for f in all_filings:
        if f["filed_date"] < CUTOFF:
            break
        if f["form"] in ("10-K", "10-Q"):
            if len(anchor_filings) < 2:
                anchor_filings.append(f)
                anchor_dates.append(datetime.strptime(f["filed_date"], "%Y-%m-%d"))

    # Find 8-K with item 2.02 near anchor dates
    earnings_8ks = []
    for f in all_filings:
        if f["filed_date"] < CUTOFF:
            break
        if f["form"] == "8-K" and "2.02" in str(f["items"]):
            fdate = datetime.strptime(f["filed_date"], "%Y-%m-%d")
            for adate in anchor_dates:
                if abs((fdate - adate).days) <= 21 or (adate - fdate).days <= 1:
                    earnings_8ks.append(f)
                    break

    eligible = anchor_filings + earnings_8ks

    # Filter out already covered
    new_filings = [f for f in eligible if f["accession"] not in covered_accessions]

    return new_filings

def extract_section(text, section_patterns, max_chars=8000):
    """Extract a section from document text matching any of the patterns."""
    for pattern in section_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            start = match.start()
            return text[start:start + max_chars].strip()
    return None

def clean_html(text):
    """Strip HTML tags and decode common entities."""
    # Remove script/style blocks
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode common entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ').replace('&#160;', ' ').replace('&quot;', '"')
    text = text.replace('&#39;', "'").replace('&apos;', "'")
    text = text.replace('&#8220;', '"').replace('&#8221;', '"')
    text = text.replace('&#8216;', "'").replace('&#8217;', "'")
    text = text.replace('&#x2019;', "'").replace('&#x2018;', "'")
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_filing_index(cik_int, accession_nodash):
    """Fetch the filing index to find exhibit documents."""
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_nodash}/{accession_nodash}-index.htm"
    time.sleep(WAIT)
    text = fetch_url(url)
    if not text:
        # Try JSON index
        url2 = f"https://data.sec.gov/submissions/index/{accession_nodash}.json"
        time.sleep(WAIT)
        text = fetch_url(url2)
    return text

def find_ex99_doc(cik_int, accession_nodash):
    """Find exhibit 99 document from filing index."""
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_int}&type=8-K&dateb=&owner=include&count=10"
    # Use the filing index JSON
    idx_url = f"https://data.sec.gov/Archives/edgar/data/{cik_int}/{accession_nodash}/{accession_nodash}-index.json"
    time.sleep(WAIT)
    text = fetch_url(idx_url)
    if text:
        try:
            data = json.loads(text)
            docs = data.get("directory", {}).get("item", [])
            for doc in docs:
                name = doc.get("name", "")
                if re.search(r'ex.?99', name, re.IGNORECASE) and name.endswith(('.htm', '.html')):
                    return name
        except Exception:
            pass

    # Try HTML index
    idx_url2 = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_nodash}/{accession_nodash}-index.htm"
    time.sleep(WAIT)
    text2 = fetch_url(idx_url2)
    if text2:
        matches = re.findall(r'href="([^"]*ex.?99[^"]*\.htm[l]?)"', text2, re.IGNORECASE)
        if matches:
            # Return just filename
            return matches[0].split("/")[-1]
    return None

def fetch_and_extract(ticker, cik, filing):
    """Fetch the filing document and extract relevant text."""
    cik_int = int(cik)
    accession = filing["accession"]
    accession_nodash = accession.replace("-", "")
    primary_doc = filing["primary_doc"]
    form = filing["form"]

    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_nodash}"
    filing_url = f"{base_url}/{primary_doc}"

    result = {
        "ticker": ticker,
        "cik": cik,
        "accession": accession,
        "form": form,
        "filed_date": filing["filed_date"],
        "primary_doc": primary_doc,
        "filing_url": filing_url,
        "extracted_text": None,
    }

    if form == "8-K":
        result["is_earnings_8k"] = True
        # Try to find ex-99 exhibit
        ex99 = find_ex99_doc(cik_int, accession_nodash)
        doc_url = f"{base_url}/{ex99}" if ex99 else filing_url
        result["filing_url"] = doc_url

        print(f"  Fetching 8-K ex99: {doc_url}")
        time.sleep(WAIT)
        text = fetch_url(doc_url)
        if text:
            clean = clean_html(text)
            # Get last 4000 chars for guidance
            result["extracted_text"] = clean[-4000:].strip()
        return result

    # 10-K or 10-Q
    print(f"  Fetching {form}: {filing_url}")
    time.sleep(WAIT)
    text = fetch_url(filing_url)
    if not text:
        return result

    clean = clean_html(text)

    if form == "10-K":
        # Item 7 - MD&A
        patterns = [
            r"item\s+7[\.\s]*management.{0,50}discussion",
            r"item\s+7[\.\s]*md&a",
            r"management.{0,20}s\s+discussion\s+and\s+analysis",
            r"item\s+7\b",
        ]
    else:  # 10-Q
        # Item 2 - MD&A
        patterns = [
            r"item\s+2[\.\s]*management.{0,50}discussion",
            r"item\s+2[\.\s]*md&a",
            r"management.{0,20}s\s+discussion\s+and\s+analysis",
            r"item\s+2\b",
        ]

    extracted = extract_section(clean, patterns, max_chars=8000)
    if not extracted:
        # Fallback: grab a middle chunk of the document
        mid = len(clean) // 3
        extracted = clean[mid:mid + 8000].strip()
        print(f"  WARNING: Could not find MD&A section for {ticker} {form}, using fallback chunk")

    result["extracted_text"] = extracted
    return result


def main():
    covered_accessions, ticker_last = load_covered_accessions()
    print(f"Loaded {len(covered_accessions)} covered accessions")

    # Priority order: missing tickers first, then others
    missing = ["ASML", "GFS", "NBIS", "TSM"]
    others = [t for t in CIK_MAP if t not in missing]
    ticker_order = missing + sorted(others)

    all_discoveries = []
    summary = {}

    for ticker in ticker_order:
        cik = CIK_MAP[ticker]
        print(f"\n=== {ticker} (CIK {cik}) ===")

        subs = get_submissions(cik)
        if not subs:
            print(f"  SKIP: could not fetch submissions")
            summary[ticker] = 0
            continue

        new_filings = find_eligible_filings(subs, ticker, covered_accessions, ticker_last)
        print(f"  Found {len(new_filings)} new eligible filings")

        if not new_filings:
            summary[ticker] = 0
            continue

        ticker_discoveries = []
        for filing in new_filings:
            print(f"  Processing {filing['form']} {filing['filed_date']} ({filing['accession']})")
            record = fetch_and_extract(ticker, cik, filing)
            ticker_discoveries.append(record)
            all_discoveries.append(record)

        summary[ticker] = len(ticker_discoveries)

    # Write output
    out_path = Path("data/filing_discovery.json")
    with open(out_path, "w") as f:
        json.dump(all_discoveries, f, indent=2)

    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(all_discoveries)} new filings discovered")
    print(f"{'='*60}")
    for ticker in ticker_order:
        count = summary.get(ticker, 0)
        if count > 0:
            print(f"  {ticker}: {count} new filing(s)")
    print(f"\nOutput written to data/filing_discovery.json")


if __name__ == "__main__":
    main()
