"""
Fetch new 10-K/10-Q and paired earnings 8-K filings from SEC EDGAR
for all tickers in CIK_MAP. Extracts MD&A / guidance text for summarization.

Outputs a JSON list to stdout: each item contains ticker, accession, form,
filed_date, and extracted_text.

Usage:
    uv run python -m jobs.fetch_new_filings > /tmp/new_filings.json
"""
from __future__ import annotations

import json
import re
import sys
import time
import logging
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup, Comment

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

USER_AGENT = "InferenceDashboard/0.1 (xelailnil@gmail.com)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
SLEEP_S = 0.15  # 150ms between requests (EDGAR cap: 10/sec)

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
    "CEG": "0001868275",
    "OKLO": "0001849056",
    "LEU": "0001065059",
}

DAYS_BACK = 395  # ~13 months to catch 4 quarters
MAX_REPORTS = 2  # 10-K/10-Q per ticker
PAIRED_8K_WINDOW = 21  # days before/after the report date to match 8-K


def _get(url: str, as_json: bool = True):
    time.sleep(SLEEP_S)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    if as_json:
        return resp.json()
    return resp.text


def _acc_dashes(raw: str) -> str:
    """Normalize to dashed accession: 0001045810-26-000021"""
    raw = raw.replace("-", "")
    return f"{raw[:10]}-{raw[10:12]}-{raw[12:]}"


def _acc_nodash(acc: str) -> str:
    return acc.replace("-", "")


def get_submissions(cik: str) -> dict:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    return _get(url, as_json=True)


def find_filings(cik: str, existing_accessions: set[str]) -> list[dict]:
    """Return list of filing dicts: {accession, form, filed_date, primary_doc, items}"""
    data = get_submissions(cik)
    recent = data.get("filings", {}).get("recent", {})
    if not recent:
        return []

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    items_list = recent.get("items", [])  # may not exist

    cutoff = (datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).date()
    results = []
    for i, form in enumerate(forms):
        try:
            fdate = datetime.strptime(dates[i], "%Y-%m-%d").date()
        except Exception:
            continue
        if fdate < cutoff:
            continue
        acc = _acc_dashes(accessions[i])
        items = items_list[i] if i < len(items_list) else ""
        if form in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            results.append({
                "accession": acc,
                "form": form.replace("/A", ""),  # treat amendments same
                "filed_date": dates[i],
                "primary_doc": primary_docs[i] if i < len(primary_docs) else "",
                "items": items,
            })
        elif form == "8-K" and "2.02" in str(items):
            results.append({
                "accession": acc,
                "form": "8-K",
                "filed_date": dates[i],
                "primary_doc": primary_docs[i] if i < len(primary_docs) else "",
                "items": items,
            })
    return results


def pair_8ks(filings: list[dict]) -> list[dict]:
    """Keep only 8-Ks that are within PAIRED_8K_WINDOW days of a 10-K/10-Q."""
    reports = [f for f in filings if f["form"] in ("10-K", "10-Q")]
    reports_sorted = sorted(reports, key=lambda x: x["filed_date"], reverse=True)[:MAX_REPORTS]
    report_dates = [datetime.strptime(r["filed_date"], "%Y-%m-%d").date() for r in reports_sorted]

    paired = []
    for f in filings:
        if f["form"] == "8-K":
            fdate = datetime.strptime(f["filed_date"], "%Y-%m-%d").date()
            for rd in report_dates:
                if abs((fdate - rd).days) <= PAIRED_8K_WINDOW:
                    paired.append(f)
                    break
    return paired


def select_new_filings(all_filings: list[dict], existing: set[str]) -> list[dict]:
    """Return the 2 most-recent 10-K/10-Q + paired 8-Ks, minus already-known ones."""
    reports = [f for f in all_filings if f["form"] in ("10-K", "10-Q")]
    reports_sorted = sorted(reports, key=lambda x: x["filed_date"], reverse=True)[:MAX_REPORTS]
    paired_8ks = pair_8ks(all_filings)
    combined = reports_sorted + [p for p in paired_8ks if p not in reports_sorted]
    return [f for f in combined if f["accession"] not in existing]


def fetch_filing_html(cik: str, accession: str, primary_doc: str) -> str:
    """Fetch the primary filing document HTML."""
    cik_int = int(cik)
    acc_nodash = _acc_nodash(accession)
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{primary_doc}"
    log.info(f"  Fetching document: {url}")
    time.sleep(SLEEP_S)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    resp.raise_for_status()
    return resp.text


def fetch_8k_exhibit(cik: str, accession: str) -> str:
    """Fetch the earnings press release exhibit (ex-99.1) from an 8-K filing."""
    cik_int = int(cik)
    acc_nodash = _acc_nodash(accession)
    # Fetch the filing index
    idx_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{acc_nodash}-index.htm"
    time.sleep(SLEEP_S)
    try:
        idx_resp = requests.get(idx_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        if idx_resp.status_code != 200:
            # Try JSON index
            json_idx_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            # fallback: just return empty
            return ""
        soup = BeautifulSoup(idx_resp.text, "lxml")
        # Find exhibit 99.1
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if re.search(r"ex.?99", href, re.IGNORECASE) and href.endswith((".htm", ".html")):
                doc_url = f"https://www.sec.gov{href}" if href.startswith("/") else href
                log.info(f"  Fetching exhibit: {doc_url}")
                time.sleep(SLEEP_S)
                doc_resp = requests.get(doc_url, headers={"User-Agent": USER_AGENT}, timeout=60)
                doc_resp.raise_for_status()
                return doc_resp.text
    except Exception as e:
        log.warning(f"  Could not fetch 8-K exhibit for {accession}: {e}")
    return ""


def clean_html(html: str) -> str:
    """Strip HTML, XBRL tags, and boilerplate; return plain text."""
    soup = BeautifulSoup(html, "lxml")
    # Remove scripts, styles, comments
    for tag in soup(["script", "style", "ix:nonnumeric", "ix:nonfraction",
                     "ix:header", "xbrli:context", "xbrli:unit"]):
        tag.decompose()
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    text = soup.get_text(separator="\n", strip=True)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def extract_mda_section(text: str, form: str) -> str:
    """Extract MD&A section from 10-K/10-Q plain text."""
    # Item 7 (10-K) or Item 2 (10-Q) — MD&A
    if form == "10-K":
        patterns = [
            r"ITEM\s*7[\.\s]+MANAGEMENT.S DISCUSSION",
            r"Item\s*7[\.\s]+Management.s Discussion",
            r"MANAGEMENT'S DISCUSSION AND ANALYSIS",
        ]
        end_patterns = [
            r"ITEM\s*7A[\.\s]+QUANTITATIVE",
            r"Item\s*7A[\.\s]+Quantitative",
            r"ITEM\s*8[\.\s]+FINANCIAL STATEMENTS",
            r"Item\s*8[\.\s]+Financial Statements",
        ]
    else:  # 10-Q
        patterns = [
            r"ITEM\s*2[\.\s]+MANAGEMENT.S DISCUSSION",
            r"Item\s*2[\.\s]+Management.s Discussion",
            r"MANAGEMENT'S DISCUSSION AND ANALYSIS",
        ]
        end_patterns = [
            r"ITEM\s*3[\.\s]+QUANTITATIVE",
            r"Item\s*3[\.\s]+Quantitative",
            r"ITEM\s*4[\.\s]+CONTROLS",
            r"Item\s*4[\.\s]+Controls",
        ]

    start = -1
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            start = m.start()
            break
    if start == -1:
        # No MD&A section found — return first 15000 chars of text
        return text[:15000]

    end = len(text)
    for pat in end_patterns:
        m = re.search(pat, text[start + 500:], re.IGNORECASE)
        if m:
            end = start + 500 + m.start()
            break

    section = text[start:end]
    # Truncate to ~25000 chars to avoid token limits
    return section[:25000]


def extract_guidance_section(text: str) -> str:
    """Extract outlook/guidance from an earnings press release."""
    # Look for outlook/guidance section
    patterns = [
        r"(?:FINANCIAL OUTLOOK|OUTLOOK|GUIDANCE|FORWARD OUTLOOK|BUSINESS OUTLOOK)",
    ]
    end_patterns = [
        r"(?:CONFERENCE CALL|ABOUT|FORWARD.LOOKING|SAFE HARBOR|NON-GAAP|RECONCIL)",
    ]

    start = -1
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            start = m.start()
            break

    if start == -1:
        # Return last 8000 chars which often has guidance
        return text[-8000:]

    end = len(text)
    for pat in end_patterns:
        m = re.search(pat, text[start + 200:], re.IGNORECASE)
        if m:
            end = start + 200 + m.start()
            break

    section = text[start:min(end, start + 8000)]
    return section


def process_ticker(ticker: str, cik: str, existing: set[str]) -> list[dict]:
    """Return list of {ticker, cik, accession, form, filed_date, extracted_text} for new filings."""
    log.info(f"Checking {ticker} (CIK {cik})")
    try:
        all_filings = find_filings(cik, existing)
    except Exception as e:
        log.error(f"  EDGAR error for {ticker}: {e}")
        return []

    new_filings = select_new_filings(all_filings, existing)
    if not new_filings:
        log.info(f"  {ticker}: no new filings")
        return []

    log.info(f"  {ticker}: {len(new_filings)} new filing(s): {[f['accession'] for f in new_filings]}")
    results = []
    for f in new_filings:
        try:
            if f["form"] == "8-K":
                html = fetch_8k_exhibit(cik, f["accession"])
                if not html:
                    # Fallback: fetch primary document
                    html = fetch_filing_html(cik, f["accession"], f["primary_doc"])
                text = clean_html(html)
                extracted = extract_guidance_section(text)
            else:
                html = fetch_filing_html(cik, f["accession"], f["primary_doc"])
                text = clean_html(html)
                extracted = extract_mda_section(text, f["form"])

            results.append({
                "ticker": ticker,
                "cik": cik,
                "accession": f["accession"],
                "form": f["form"],
                "filed_date": f["filed_date"],
                "extracted_text": extracted,
            })
        except Exception as e:
            log.error(f"  Failed to fetch {ticker} {f['accession']}: {e}")
            results.append({
                "ticker": ticker,
                "cik": cik,
                "accession": f["accession"],
                "form": f["form"],
                "filed_date": f["filed_date"],
                "extracted_text": f"[FETCH ERROR: {e}]",
            })
    return results


def main():
    # Load existing summaries
    summaries_path = "/home/user/Inference-Dashboard/data/filing_summaries.json"
    try:
        with open(summaries_path) as f:
            existing_summaries = json.load(f)
    except FileNotFoundError:
        existing_summaries = {}
    existing_accessions = set(existing_summaries.keys())
    log.info(f"Existing summaries: {len(existing_accessions)} entries")

    all_new = []
    for ticker, cik in sorted(CIK_MAP.items()):
        new = process_ticker(ticker, cik, existing_accessions)
        all_new.extend(new)
        # Small extra delay between tickers
        time.sleep(0.1)

    log.info(f"\nTotal new filings found: {len(all_new)}")
    for item in all_new:
        log.info(f"  {item['ticker']} {item['form']} {item['accession']} {item['filed_date']}")

    # Write to stdout as JSON (extracted_text truncated in log but full in output)
    print(json.dumps(all_new, indent=2))


if __name__ == "__main__":
    main()
