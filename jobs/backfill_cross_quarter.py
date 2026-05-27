"""
Backfill cross_quarter.json for every ticker that has 2+ entries in
filing_summaries.json but no entry in cross_quarter.json.
Requires ANTHROPIC_API_KEY in the environment.
"""

import json
import os
import re
import time
from datetime import date
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
FILING_SUMMARIES = DATA / "filing_summaries.json"
CROSS_QUARTER = DATA / "cross_quarter.json"
TODAY = date.today().isoformat()


def save_json(path: Path, obj):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    tmp.rename(path)


def make_cross_quarter_prompt(ticker: str, entries: list[dict]) -> str:
    entries_text = ""
    for e in reversed(entries):  # oldest first in context, clearest for trend reading
        entries_text += f"\n\n--- {e['form']} filed {e['filed_date']} ({e['accession']}) ---\n"
        entries_text += f"TL;DR: {e['tldr']}\n"
        entries_text += "Takeaways:\n" + "\n".join(f"  - {t}" for t in e.get('takeaways', [])) + "\n"
        g = e.get('guidance')
        if g:
            entries_text += (
                f"Guidance: {g.get('period', '')}: "
                f"Rev={g.get('revenue', '')}, GM={g.get('gross_margin', '')}\n"
            )
        q = e.get('quote', '')
        if q:
            entries_text += f'Quote: "{q}"\n'

    accessions_str = json.dumps([e['accession'] for e in reversed(entries)])
    today = TODAY

    return f"""You are synthesizing SEC filings for an AI inference stack investing dashboard.

Ticker: {ticker}
Today: {today}
Filings available (oldest → newest):
{entries_text}

Return ONLY valid JSON (no markdown, no commentary) matching exactly this schema:

{{
  "as_of": "{today}",
  "based_on_accessions": {accessions_str},
  "covers": "<oldest period> → <newest period, e.g. Q1 FY25 → FY25 10-K → Q1 FY26>",
  "headline": "<one-line net change across the window — NOT a description of the latest filing>",
  "shifts": [
    {{
      "area": "<lowercase from: growth margins concentration supply capex guidance china segments leverage capital_returns regulation>",
      "direction": "<lowercase from: accelerating decelerating stable raised lowered tightening easing improving deteriorating tight flat expanding contracting unchanged>",
      "trend": "<numeric progression across filings, e.g. '73.5% → 74% → 73.5%'; must reference at least 2 filings>",
      "note": "<optional 1-line interpretation; empty string is fine>"
    }}
  ],
  "verdict": "<one-line: does this change unlock, kill, or leave the investing thesis intact? Must say something the headline doesn't>"
}}

Rules you must follow:
- headline: net directional change across the FULL window, not a recap of the last filing
- shifts: 4-7 entries. SKIP any shift you can only evidence from one filing.
- trend: prefer concrete numbers ("$8.5B → $7.1B → $6.2B") over adjectives. Reference at least 2 filings.
- area vocab: growth, margins, concentration, supply, capex, guidance, china, segments, leverage, capital_returns, regulation
- direction vocab: accelerating, decelerating, stable, raised, lowered, tightening, easing, improving, deteriorating, tight, flat, expanding, contracting, unchanged
- verdict: must answer "unlock / kill / intact?" and say something distinct from the headline
- covers: list periods from oldest to newest (e.g. "Q1 FY25 → FY25 10-K → Q1 FY26")
- 4 strong, evidenced shifts beats 7 weak ones"""


def synthesize(ticker: str, entries: list[dict], client: anthropic.Anthropic) -> dict | None:
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
    except json.JSONDecodeError as e:
        print(f"  JSON parse error for {ticker}: {e}")
        return None
    except Exception as e:
        print(f"  Claude API error for {ticker}: {e}")
        return None


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    client = anthropic.Anthropic(api_key=api_key)

    summaries = json.loads(FILING_SUMMARIES.read_text())
    cross_quarter = json.loads(CROSS_QUARTER.read_text()) if CROSS_QUARTER.exists() else {}

    # Group summaries by ticker
    from collections import defaultdict
    by_ticker = defaultdict(list)
    for acc, entry in summaries.items():
        by_ticker[entry['ticker']].append(entry)

    # Find tickers missing from cross_quarter with 2+ entries
    to_process = []
    for ticker, entries in sorted(by_ticker.items()):
        if len(entries) >= 2 and ticker not in cross_quarter:
            to_process.append(ticker)

    print(f"Tickers to backfill in cross_quarter.json: {len(to_process)}")
    print(f"Already in cross_quarter.json: {sorted(cross_quarter.keys())}")
    print()

    if not to_process:
        print("Nothing to do.")
        return []

    processed = []
    for ticker in to_process:
        entries = sorted(by_ticker[ticker], key=lambda x: x['filed_date'], reverse=True)[:4]
        print(f"Synthesizing {ticker} ({len(entries)} filings: {[e['filed_date'] for e in entries]})...")
        result = synthesize(ticker, entries, client)
        if result:
            # Ensure required fields
            result['as_of'] = TODAY
            result.setdefault('based_on_accessions', [e['accession'] for e in reversed(entries)])
            cross_quarter[ticker] = result
            save_json(CROSS_QUARTER, cross_quarter)
            print(f"  OK: {result.get('headline', '')[:90]}")
            processed.append(ticker)
            # Small pause to avoid rate-limiting
            time.sleep(0.5)
        else:
            print(f"  FAILED — skipping {ticker}")

    print(f"\nDone. Backfilled {len(processed)} tickers: {processed}")
    return processed


if __name__ == "__main__":
    main()
