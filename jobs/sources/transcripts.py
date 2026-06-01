"""Earnings-call transcript scraper.

Pulls the latest transcript per ticker from earningscalls.dev — a free
web aggregator (Nasdaq-fed, no signup) with global coverage of US-listed
tickers including ADRs (TSM, ASML).

The point of this source is NOT new filings — EDGAR already covers those.
The point is the analyst Q&A and shareholder/analyst calls that don't get
filed as 8-Ks, where management's narrative on supply / demand / capex
actually drifts quarter to quarter.

Storage model:
  data/transcripts/{ticker}-{call_id}.json   — one file per call (immutable
      once written; call_id is earningscalls.dev's stable integer ID)
  data/transcripts_index.json                — per-ticker latest pointer +
      coverage stats, read by the frontend and the narrative-tracking stage

We rely on the redirect pattern:
  GET https://earningscalls.dev/transcripts/{TICKER}
      -> 302 Location: /transcript/{call_id}
On the destination page, content is in `.speaker-segment` divs with
`.speaker-name`, `.speaker-role`, `.speaker-text` children, plus an
`info-item` table with the call date / sector / industry. The page also
declares the call type in an <h2> ("Earnings Call", "Shareholder/Analyst
Call", etc.) — we preserve it so downstream can filter.

Non-US tickers map to their US-listed ADR symbol via ADR_MAP. Unmapped
local tickers (CN A-shares, TW small caps, JP non-ADR names, KR locals)
return no data — documented as a coverage gap for the about page.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
BASE = "https://earningscalls.dev"

# Local exchange ticker → US-listed symbol on earningscalls.dev.
# Only entries verified to redirect are listed; the rest are intentional gaps.
ADR_MAP: dict[str, str] = {
    # TSM/ASML/ASX/NBIS already use US tickers in seed.py, so no mapping needed.
    # Add verified non-US → ADR resolutions here as we discover them.
}

# Calls older than this are skipped — narrative drift loses signal beyond a year.
MAX_AGE_DAYS = 400


@dataclass
class TranscriptResult:
    fetched: list[dict] = field(default_factory=list)   # net new this run
    cached: list[str] = field(default_factory=list)     # already on disk
    errors: dict[str, str] = field(default_factory=dict)
    rate_limited: list[str] = field(default_factory=list)
    unmapped: list[str] = field(default_factory=list)


def _resolve_symbol(ticker: str) -> str | None:
    """Map a local-exchange ticker to the symbol earningscalls.dev uses.
    Returns None if we know there's no ADR coverage."""
    if "." not in ticker:
        return ticker  # US listing — pass through
    return ADR_MAP.get(ticker)


def _latest_call_id(session, symbol: str) -> tuple[int | None, int]:
    """Probe /transcripts/{SYMBOL} and return (call_id, http_status).
    302 → extract id from Location. 200/404/429 → (None, status)."""
    r = session.get(f"{BASE}/transcripts/{symbol}", allow_redirects=False, timeout=15)
    if r.status_code == 302:
        loc = r.headers.get("Location", "")
        m = re.search(r"/transcript/(\d+)", loc)
        if m:
            return int(m.group(1)), 302
    return None, r.status_code


def _parse_transcript_page(html: str) -> dict:
    """Extract structured fields from a /transcript/{id} HTML page."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    company = h1.get_text(strip=True) if h1 else None
    h2 = soup.find("h2")
    call_type = h2.get_text(strip=True) if h2 else None
    # H2 reads either "{Company} - {CallType}" (dash separator, e.g. NVDA) or
    # "{Company}, {CallType}, {Date}" (comma separator, e.g. TSM/ASML/MU).
    # Strip the company prefix, drop the trailing date suffix if any.
    if call_type and company and call_type.startswith(company):
        call_type = call_type[len(company):].lstrip(" -–—,").strip()
        # Comma-separated form: keep only the call-type segment (drop date)
        if "," in call_type:
            parts = [p.strip() for p in call_type.split(",")]
            # The call-type segment is the one containing "Call" or "Earnings"
            for part in parts:
                if "Call" in part or "Earnings" in part:
                    call_type = part
                    break

    # info-item rows: Date / Sector / Industry
    info: dict[str, str] = {}
    for item in soup.select(".info-item"):
        label = item.select_one(".label")
        value = item.select_one(".value")
        if label and value:
            info[label.get_text(strip=True).rstrip(":").lower()] = value.get_text(strip=True)

    # Parse the human date ("Tuesday, March 17, 2026") into ISO.
    iso_date = None
    raw_date = info.get("date")
    if raw_date:
        for fmt in ("%A, %B %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
            try:
                iso_date = datetime.strptime(raw_date.strip(), fmt).date().isoformat()
                break
            except ValueError:
                continue

    segments: list[dict] = []
    for seg in soup.select(".speaker-segment"):
        name_el = seg.select_one(".speaker-name")
        role_el = seg.select_one(".speaker-role")
        text_el = seg.select_one(".speaker-text")
        if not text_el:
            continue
        segments.append({
            "speaker": name_el.get_text(strip=True) if name_el else None,
            "role": role_el.get_text(strip=True) if role_el else None,
            "text": text_el.get_text(" ", strip=True),
        })

    return {
        "company": company,
        "call_type": call_type,
        "date": iso_date,
        "raw_date": raw_date,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "segments": segments,
        "word_count": sum(len(s["text"].split()) for s in segments),
    }


def _store_path(data_dir: Path, ticker: str, call_id: int) -> Path:
    safe = ticker.replace("/", "_").replace(":", "_")
    return data_dir / f"{safe}-{call_id}.json"


def fetch(
    tickers: list[str],
    data_dir: Path,
    sleep_between: float = 2.5,
    max_429_retries: int = 2,
) -> TranscriptResult:
    """Fetch the latest transcript for each ticker; cache by call_id.

    `sleep_between` paces requests politely — earningscalls.dev starts
    returning 429 after ~20 rapid requests. 2.5s spacing has been stable
    in practice.
    """
    import requests

    data_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})

    result = TranscriptResult()
    cutoff = datetime.now(timezone.utc).date().toordinal() - MAX_AGE_DAYS

    for ticker in tickers:
        symbol = _resolve_symbol(ticker)
        if symbol is None:
            result.unmapped.append(ticker)
            log.debug("Skip %s (no ADR mapping)", ticker)
            continue

        # 1. Latest-call probe (with one 429 retry).
        call_id: int | None = None
        for attempt in range(max_429_retries + 1):
            try:
                call_id, status = _latest_call_id(session, symbol)
            except Exception as e:
                result.errors[ticker] = f"probe failed: {e}"
                log.warning("FAIL transcripts %s: %s", ticker, e)
                break
            if call_id is not None:
                break
            if status == 429:
                wait = sleep_between * (attempt + 2)
                log.info("RATE_LIMIT %s — sleeping %.1fs", ticker, wait)
                time.sleep(wait)
                continue
            if status == 404:
                # Unknown symbol — record and move on (don't keep retrying).
                result.errors[ticker] = "not found on earningscalls.dev"
                break
            result.errors[ticker] = f"http {status}"
            break

        if call_id is None:
            if ticker not in result.errors:
                result.rate_limited.append(ticker)
            time.sleep(sleep_between)
            continue

        # 2. Cache hit?
        out_path = _store_path(data_dir, ticker, call_id)
        if out_path.exists():
            result.cached.append(ticker)
            log.debug("CACHED %s call_id=%d", ticker, call_id)
            # Still sleep — keeps subsequent probes polite.
            time.sleep(sleep_between)
            continue

        # 3. Fetch the transcript HTML.
        try:
            r = session.get(f"{BASE}/transcript/{call_id}", timeout=20)
            if r.status_code != 200:
                result.errors[ticker] = f"transcript page http {r.status_code}"
                time.sleep(sleep_between)
                continue
            parsed = _parse_transcript_page(r.text)
        except Exception as e:
            result.errors[ticker] = f"parse failed: {e}"
            log.warning("FAIL transcripts parse %s: %s", ticker, e)
            time.sleep(sleep_between)
            continue

        # 4. Age filter. Skip writing undated calls too — without a parseable
        # date the age filter can't run and a null date pollutes downstream
        # (narrative sort, and transform.merge's date sort). Better to drop it
        # and re-fetch once the date format is supported.
        if not parsed.get("date"):
            log.info("NODATE %s call_id=%d — unparseable date, skipping write", ticker, call_id)
            time.sleep(sleep_between)
            continue
        try:
            d = datetime.strptime(parsed["date"], "%Y-%m-%d").date()
            if d.toordinal() < cutoff:
                log.info("STALE %s call_id=%d date=%s — skipping write", ticker, call_id, parsed["date"])
                time.sleep(sleep_between)
                continue
        except ValueError:
            pass

        entry = {
            "ticker": ticker,
            "symbol_used": symbol,
            "call_id": call_id,
            "source": "earningscalls.dev",
            "url": f"{BASE}/transcript/{call_id}",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            **parsed,
        }

        # 5. Atomic write.
        import json
        tmp = out_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(out_path)
        result.fetched.append(entry)
        log.info("OK transcripts %s: call_id=%d, %s, %d segments, %d words",
                 ticker, call_id, parsed.get("call_type") or "?",
                 len(parsed.get("segments") or []), parsed.get("word_count") or 0)

        time.sleep(sleep_between)

    return result


def build_index(data_dir: Path) -> dict:
    """Aggregate all per-call JSONs into a per-ticker index for the frontend."""
    import json
    by_ticker: dict[str, list[dict]] = {}
    if not data_dir.exists():
        return {"by_ticker": {}, "total_calls": 0, "tickers_covered": 0}
    for p in sorted(data_dir.glob("*.json")):
        try:
            entry = json.loads(p.read_text())
        except Exception:
            continue
        t = entry.get("ticker")
        if not t:
            continue
        by_ticker.setdefault(t, []).append({
            "call_id": entry.get("call_id"),
            "call_type": entry.get("call_type"),
            "date": entry.get("date"),
            "url": entry.get("url"),
            "segments": len(entry.get("segments") or []),
            "word_count": entry.get("word_count"),
            "source": entry.get("source"),
        })
    # Sort each ticker's history newest-first.
    for t, calls in by_ticker.items():
        calls.sort(key=lambda c: c.get("date") or "", reverse=True)
    return {
        "by_ticker": by_ticker,
        "total_calls": sum(len(v) for v in by_ticker.values()),
        "tickers_covered": len(by_ticker),
    }
