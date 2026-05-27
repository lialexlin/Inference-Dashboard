"""
Daily filing summarizer — fetches new 10-K/10-Q/earnings-8-K filings for all
US-listed tickers in CIK_MAP and generates structured JSON summaries via Claude.
Writes data/filing_summaries.json and data/cross_quarter.json.
"""

import json
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import anthropic
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
FILING_SUMMARIES = DATA / "filing_summaries.json"
CROSS_QUARTER = DATA / "cross_quarter.json"

USER_AGENT = "InferenceDashboard/0.1 (xelailnil@gmail.com)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
PAUSE = 0.15  # seconds between EDGAR requests
TODAY = date.today().isoformat()

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

VALID_LAYERS = [
    "hbm", "foundry", "packaging", "wfe", "gpu", "networking", "optics",
    "switches", "power", "cooling", "hyperscalers", "neoclouds", "software",
    "eda", "substrates",
]

# Layer tags per ticker (primary + secondary)
TICKER_LAYERS = {
    "MU": ["hbm", "foundry"],
    "TSM": ["foundry"],
    "INTC": ["foundry", "gpu"],
    "GFS": ["foundry"],
    "AMKR": ["packaging"],
    "ASML": ["wfe"],
    "AMAT": ["wfe"],
    "LRCX": ["wfe"],
    "KLAC": ["wfe"],
    "NVDA": ["gpu", "networking"],
    "AMD": ["gpu"],
    "AVGO": ["networking", "gpu"],
    "MRVL": ["networking", "hbm"],
    "GOOGL": ["hyperscalers", "neoclouds"],
    "LITE": ["optics"],
    "COHR": ["optics"],
    "FN": ["optics", "networking"],
    "MXL": ["networking", "switches"],
    "ANET": ["networking", "switches"],
    "CSCO": ["networking", "switches"],
    "HPE": ["networking", "neoclouds"],
    "CLS": ["neoclouds"],
    "GEV": ["power"],
    "ETN": ["power"],
    "VRT": ["power", "cooling"],
    "GNRC": ["power"],
    "CMI": ["power"],
    "HUBB": ["power"],
    "PWR": ["power"],
    "CAT": ["power"],
    "NVT": ["power", "cooling"],
    "MOD": ["cooling"],
    "MSFT": ["hyperscalers", "neoclouds"],
    "META": ["hyperscalers"],
    "AMZN": ["hyperscalers", "neoclouds"],
    "ORCL": ["hyperscalers", "neoclouds"],
    "CRWV": ["neoclouds"],
    "NBIS": ["neoclouds"],
    "CRM": ["software"],
    "NOW": ["software"],
    "SNOW": ["software"],
    "PLTR": ["software"],
    "CDNS": ["eda"],
    "SNPS": ["eda"],
    "CEG": ["power"],
    "OKLO": ["power"],
    "LEU": ["power"],
}


# ---------------------------------------------------------------------------
# Load / save helpers
# ---------------------------------------------------------------------------

def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, obj):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    tmp.rename(path)


# ---------------------------------------------------------------------------
# EDGAR helpers
# ---------------------------------------------------------------------------

def edgar_get(url: str) -> dict | None:
    time.sleep(PAUSE)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  EDGAR GET error {url}: {e}")
        return None


def filing_url(cik: str, accession: str, primary_doc: str) -> str:
    acc_nodash = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{primary_doc}"


def fetch_html(url: str) -> str | None:
    time.sleep(PAUSE)
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  HTML GET error {url}: {e}")
        return None


def parse_filing_text(html: str, form: str) -> str:
    """Strip HTML and return relevant text for summarization (cap at ~40k chars)."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove script, style, XBRL inline tags
        for tag in soup(["script", "style", "ix:nonfraction", "ix:nonnumeric",
                          "ix:header", "ix:continuation"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Collapse excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text[:45000]
    except Exception as e:
        print(f"  parse error: {e}")
        return html[:45000]


def find_earnings_exhibit(cik: str, accession: str) -> str | None:
    """Return URL of ex-99.1 exhibit from an 8-K filing index."""
    acc_nodash = accession.replace("-", "")
    cik_int = int(cik)
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{accession}-index.htm"
    time.sleep(PAUSE)
    try:
        r = requests.get(index_url, headers={"User-Agent": USER_AGENT}, timeout=20)
        if r.status_code != 200:
            # Try JSON index
            index_url2 = f"https://data.sec.gov/submissions/CIK{cik}.json"
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            name = href.lower()
            if re.search(r'ex[\-_]?99', name) and name.endswith(('.htm', '.html')):
                return f"https://www.sec.gov{href}" if href.startswith('/') else href
    except Exception as e:
        print(f"  Index fetch error: {e}")
    return None


def get_new_filings(ticker: str, cik: str, existing_accessions: set,
                    cutoff_days: int = 400) -> list[dict]:
    """Return list of new filing dicts not already in existing_accessions."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = edgar_get(url)
    if not data:
        return []

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    items_list = recent.get("items", [])

    cutoff = (date.today() - timedelta(days=cutoff_days))

    # Pass 1: find 10-K and 10-Q filings within window
    reports = []
    for i, (form, fdate, acc, pdoc) in enumerate(zip(forms, dates, accessions, primary_docs)):
        if form not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            continue
        try:
            fd = date.fromisoformat(fdate)
        except ValueError:
            continue
        if fd < cutoff:
            break  # EDGAR returns newest first; once past cutoff, done
        if acc in existing_accessions:
            continue
        reports.append({
            "ticker": ticker,
            "cik": cik,
            "form": form.replace("/A", ""),  # normalize amendments
            "filed_date": fdate,
            "accession": acc,
            "primary_doc": pdoc,
            "type": "report",
        })
        if len(reports) >= 2:
            break  # cap at 2 most recent

    # Pass 2: find paired earnings 8-Ks
    report_dates = {date.fromisoformat(r["filed_date"]) for r in reports}
    # Also include already-existing report dates for pairing
    existing_report_dates = set()
    # (We'll handle this in the caller)

    earnings_8ks = []
    for i, (form, fdate, acc, pdoc, items) in enumerate(zip(
            forms, dates, accessions, primary_docs, items_list)):
        if form != "8-K":
            continue
        if "2.02" not in str(items):
            continue
        if acc in existing_accessions:
            continue
        try:
            fd = date.fromisoformat(fdate)
        except ValueError:
            continue
        if fd < cutoff:
            break
        # Check if within ±1 day of a report date
        for rd in report_dates:
            if abs((fd - rd).days) <= 1:
                earnings_8ks.append({
                    "ticker": ticker,
                    "cik": cik,
                    "form": "8-K",
                    "filed_date": fdate,
                    "accession": acc,
                    "primary_doc": pdoc,
                    "type": "earnings_8k",
                })
                break

    return reports + earnings_8ks


# ---------------------------------------------------------------------------
# Claude summarizer
# ---------------------------------------------------------------------------

def make_summary_prompt(ticker: str, form: str, filed_date: str,
                        filing_text: str, hint_layers: list[str]) -> str:
    layers_hint = ", ".join(hint_layers)
    schema = """Return ONLY valid JSON matching exactly this schema (no markdown, no commentary):
{
  "accession": "<filled by caller>",
  "ticker": "<ticker>",
  "form": "<form>",
  "filed_date": "<filed_date>",
  "tldr": "1-2 sentence headline summary of what is most important",
  "takeaways": [
    "4-8 concrete, quantitative bullet points",
    "Focus on: demand mix, capacity, supply chain, customer concentration, capex",
    "Call out new product cadence, China/export-control impacts with dollar amounts",
    "Call out segment growth rates (Data Center, Networking, Gaming, etc.)"
  ],
  "guidance": null,
  "layer_tags": ["1-3 layer ids from the valid list"],
  "quote": "single most quotable sentence from the filing, ~150-250 chars, exact wording",
  "quote_section": "section name where quote was found"
}"""

    return f"""You are summarizing an SEC filing for an AI inference stack investing dashboard.

Ticker: {ticker}
Form: {form}
Filed: {filed_date}
Suggested layer tags (confirm or adjust based on content): {layers_hint}
Valid layer IDs: hbm, foundry, packaging, wfe, gpu, networking, optics, switches, power, cooling, hyperscalers, neoclouds, software, eda, substrates

Filing text (first ~40k chars):
---
{filing_text}
---

{schema}

Rules:
- takeaways: 4-8 bullets, each concrete and quantitative where possible
- guidance: null for 10-K/10-Q (guidance is in the paired 8-K)
- layer_tags: 1-3 IDs only from the valid list above
- quote: pick the most quotable sentence about demand, bottleneck, or supply; ~150-250 chars; exact wording
- If it's a 10-K or 10-Q, set guidance to null
- Be specific: numbers > adjectives"""


def make_8k_summary_prompt(ticker: str, filed_date: str, filing_text: str,
                            hint_layers: list[str]) -> str:
    layers_hint = ", ".join(hint_layers)
    schema = """Return ONLY valid JSON (no markdown, no commentary):
{
  "accession": "<filled by caller>",
  "ticker": "<ticker>",
  "form": "8-K",
  "filed_date": "<filed_date>",
  "tldr": "1-2 sentence summary of the earnings release headline",
  "takeaways": [
    "4-8 concrete quantitative bullets about results and guidance"
  ],
  "guidance": {
    "period": "Q<N> FY<YY> or Full Year FY<YY>",
    "revenue": "$X.XB ± Y%",
    "gross_margin": "XX% GAAP/non-GAAP",
    "opex": "$X.XB if provided",
    "notes": "one-line context or null"
  },
  "layer_tags": ["1-3 layer ids"],
  "quote": "most quotable sentence about outlook or demand, ~150-250 chars exact",
  "quote_section": "Outlook or Forward Guidance"
}"""

    return f"""You are summarizing an earnings press release (SEC 8-K) for an AI inference stack investing dashboard.

Ticker: {ticker}
Filed: {filed_date}
Suggested layer tags: {layers_hint}
Valid layer IDs: hbm, foundry, packaging, wfe, gpu, networking, optics, switches, power, cooling, hyperscalers, neoclouds, software, eda, substrates

Earnings release text:
---
{filing_text}
---

{schema}

Rules:
- guidance: populate from the Outlook/guidance section. If no guidance found, set to null and note in tldr
- Be precise with guidance numbers (use company's exact framing: GAAP vs non-GAAP)
- takeaways should cover: actual results vs guidance, key segment performance, notable one-timers, and forward guidance
- quote: the single most quotable forward-looking sentence from management"""


def summarize_with_claude(prompt: str, client: anthropic.Anthropic) -> dict | None:
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        # Strip markdown code blocks if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"  Claude API error: {e}")
        return None


# ---------------------------------------------------------------------------
# Cross-quarter synthesis
# ---------------------------------------------------------------------------

def make_cross_quarter_prompt(ticker: str, entries: list[dict]) -> str:
    entries_text = ""
    for e in entries:
        entries_text += f"\n\n--- {e['form']} filed {e['filed_date']} ({e['accession']}) ---\n"
        entries_text += f"TL;DR: {e['tldr']}\n"
        entries_text += "Takeaways:\n" + "\n".join(f"  - {t}" for t in e['takeaways']) + "\n"
        if e.get('guidance'):
            g = e['guidance']
            entries_text += f"Guidance: {g.get('period','')}: Rev={g.get('revenue','')}, GM={g.get('gross_margin','')}\n"
        if e.get('quote'):
            q = e['quote']
            entries_text += f'Quote: "{q}"\n'

    schema = """Return ONLY valid JSON (no markdown):
{
  "as_of": "<today ISO date>",
  "based_on_accessions": ["acc1", "acc2", ...],
  "covers": "Q<N> FY<YY> → FY<YY> 10-K → Q<N> FY<YY>",
  "headline": "one-line plain-English net change across all filings",
  "shifts": [
    {
      "area": "<from controlled vocab>",
      "direction": "<from controlled vocab>",
      "trend": "numeric progression across filings e.g. '73.5% → 74% → 73.5%'",
      "note": "optional interpretation"
    }
  ],
  "verdict": "one-line: does this unlock, kill, or leave the thesis intact?"
}"""

    return f"""You are synthesizing SEC filings for an AI inference stack investing dashboard.

Ticker: {ticker}
Today: {TODAY}

Filings (newest first):
{entries_text}

{schema}

Rules:
- headline: NET change across the window, NOT a description of the latest filing alone
- shifts: 4-7 entries, each referencing at least 2 filings with numeric progression
- area vocab: growth, margins, concentration, supply, capex, guidance, china, segments, leverage, capital_returns, regulation
- direction vocab: accelerating, decelerating, stable, raised, lowered, tightening, easing, improving, deteriorating, tight, flat, expanding, contracting, unchanged
- trend: prefer numbers "73.5% → 74%" over adjectives; reference at least 2 filings
- verdict: must say something different from headline; answer "unlock / kill / intact?"
- covers: e.g. "Q1 FY25 → FY25 10-K → Q1 FY26" (from oldest to newest)
- Skip any shift you can only evidence from 1 filing
- based_on_accessions: include all accessions used (2-4)"""


def synthesize_cross_quarter(ticker: str, entries: list[dict],
                              client: anthropic.Anthropic) -> dict | None:
    if len(entries) < 2:
        return None
    prompt = make_cross_quarter_prompt(ticker, entries)
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
        return json.loads(raw)
    except Exception as e:
        print(f"  Cross-quarter synthesis error for {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    client = anthropic.Anthropic(api_key=api_key)

    # Load existing data
    summaries = load_json(FILING_SUMMARIES, {})
    cross_quarter = load_json(CROSS_QUARTER, {})
    existing_accessions = set(summaries.keys())

    print(f"Existing summaries: {len(summaries)}")
    print(f"Today: {TODAY}")
    print()

    new_filings = []  # list of (ticker, filing_dict)
    check_count = 0

    # Phase 1: discover new filings
    for ticker, cik in sorted(CIK_MAP.items()):
        print(f"Checking {ticker} (CIK {cik})...")
        check_count += 1
        filings = get_new_filings(ticker, cik, existing_accessions)
        if filings:
            print(f"  Found {len(filings)} new filing(s): {[f['accession'] for f in filings]}")
            for f in filings:
                new_filings.append(f)
        else:
            print(f"  No new filings")

    print(f"\nChecked {check_count} tickers. Found {len(new_filings)} new filings total.")

    if not new_filings:
        print("Nothing to do — exiting cleanly.")
        return

    # Phase 2: fetch and summarize
    processed_accessions = []
    tickers_updated = set()

    for filing in new_filings:
        ticker = filing["ticker"]
        cik = filing["cik"]
        form = filing["form"]
        filed_date = filing["filed_date"]
        accession = filing["accession"]
        primary_doc = filing["primary_doc"]
        ftype = filing["type"]

        print(f"\nProcessing {ticker} {form} {filed_date} ({accession})...")

        # Fetch document
        if ftype == "earnings_8k":
            # First try to find ex-99.1 exhibit
            exhibit_url = find_earnings_exhibit(cik, accession)
            if exhibit_url:
                print(f"  Fetching exhibit: {exhibit_url}")
                html = fetch_html(exhibit_url)
            else:
                # Fall back to primary document
                doc_url = filing_url(cik, accession, primary_doc)
                print(f"  Fetching primary doc: {doc_url}")
                html = fetch_html(doc_url)
        else:
            doc_url = filing_url(cik, accession, primary_doc)
            print(f"  Fetching: {doc_url}")
            html = fetch_html(doc_url)

        if not html:
            print(f"  SKIP: could not fetch document")
            continue

        filing_text = parse_filing_text(html, form)
        print(f"  Parsed text: {len(filing_text)} chars")

        # Build prompt
        hint_layers = TICKER_LAYERS.get(ticker, ["software"])
        if ftype == "earnings_8k":
            prompt = make_8k_summary_prompt(ticker, filed_date, filing_text, hint_layers)
        else:
            prompt = make_summary_prompt(ticker, form, filed_date, filing_text, hint_layers)

        # Summarize
        print(f"  Calling Claude...")
        summary = summarize_with_claude(prompt, client)

        if not summary:
            print(f"  SKIP: Claude summary failed")
            continue

        # Inject accession (Claude doesn't know it)
        summary["accession"] = accession
        summary["ticker"] = ticker
        summary["form"] = form
        summary["filed_date"] = filed_date

        # Validate layer_tags
        valid_tags = [t for t in summary.get("layer_tags", []) if t in VALID_LAYERS]
        if not valid_tags:
            valid_tags = hint_layers[:1]
        summary["layer_tags"] = valid_tags

        # Save
        summaries[accession] = summary
        processed_accessions.append(accession)
        tickers_updated.add(ticker)
        print(f"  OK: {summary['tldr'][:80]}...")

        # Atomic write after each filing (so partial runs persist)
        save_json(FILING_SUMMARIES, summaries)

    print(f"\nProcessed {len(processed_accessions)} filings. Updating cross_quarter for {len(tickers_updated)} tickers...")

    # Phase 3: cross-quarter synthesis for affected tickers
    for ticker in sorted(tickers_updated):
        print(f"\nSynthesizing cross-quarter for {ticker}...")
        # Gather all entries for this ticker sorted newest first
        ticker_entries = sorted(
            [v for v in summaries.values() if v["ticker"] == ticker],
            key=lambda x: x["filed_date"],
            reverse=True,
        )[:4]  # max 4

        if len(ticker_entries) < 2:
            print(f"  Only {len(ticker_entries)} filing(s) — skipping cross-quarter")
            continue

        synthesis = synthesize_cross_quarter(ticker, ticker_entries, client)
        if synthesis:
            cross_quarter[ticker] = synthesis
            save_json(CROSS_QUARTER, cross_quarter)
            print(f"  OK: {synthesis.get('headline', '')[:80]}...")
        else:
            print(f"  SKIP: synthesis failed")

    print(f"\n=== DONE ===")
    print(f"New filings processed: {len(processed_accessions)}")
    print(f"Tickers with updated cross-quarter: {len(tickers_updated)}")
    for acc in processed_accessions:
        s = summaries[acc]
        print(f"  {s['ticker']} {s['form']} {s['filed_date']} ({acc})")

    return processed_accessions, tickers_updated


if __name__ == "__main__":
    main()
