"""Daily refresh orchestrator.

Pulls live data from all sources, tags signals, merges with curated seed data,
and atomically rewrites data/*.json.

Usage:
    python -m jobs.refresh                # full refresh
    python -m jobs.refresh --skip-rss     # for fast local iteration
    python -m jobs.refresh --skip-edgar
    python -m jobs.refresh --tickers AAPL,MSFT  # subset (debug)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from jobs import seed
from jobs import transform
from jobs.sources import prices as prices_src
from jobs.sources import rss as rss_src
from jobs.sources import edgar as edgar_src

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def _load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--skip-prices", action="store_true")
    p.add_argument("--skip-rss", action="store_true")
    p.add_argument("--skip-edgar", action="store_true")
    p.add_argument("--tickers", help="comma-separated ticker subset for prices/edgar (debug)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    log = logging.getLogger("refresh")

    # Seed if data/ is empty (idempotent — running it costs ~50ms)
    if not (DATA / "layers.json").exists():
        log.info("Seeding (data/ missing) ...")
        seed.main()

    layers = _load_json(DATA / "layers.json", [])
    players = _load_json(DATA / "players.json", [])
    if not layers or not players:
        log.error("Run `python -m jobs.seed` first.")
        return 1

    tickers = [p["ticker"] for p in players]
    if args.tickers:
        wanted = set(args.tickers.split(","))
        tickers = [t for t in tickers if t in wanted]

    # Preserve previous-run source blocks so partial refreshes (--skip-*)
    # don't blank out unrelated stats on the about page.
    prev_meta = _load_json(DATA / "meta.json", {})
    meta = {
        "last_refresh_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
        "sources": dict(prev_meta.get("sources", {})),
    }

    # Prices + fundamentals -----------------------------------------------
    if not args.skip_prices:
        log.info("Fetching prices for %d tickers ...", len(tickers))
        pr = prices_src.fetch(tickers)
        _write_json(DATA / "prices.json", pr.prices)
        _write_json(DATA / "fundamentals.json", pr.fundamentals)
        meta["sources"]["prices"] = {
            "ok": len(pr.prices),
            "errors": pr.errors,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        log.info("Prices: %d ok, %d errors", len(pr.prices), len(pr.errors))
    else:
        log.info("Skipping prices.")

    # RSS feeds ----------------------------------------------------------
    discovered: list[dict] = []
    if not args.skip_rss:
        log.info("Fetching RSS feeds ...")
        rr = rss_src.fetch()
        discovered.extend(rr.entries)
        meta["sources"]["rss"] = {
            "ok": sum(1 for v in rr.per_source_counts.values() if v > 0),
            "total_entries": len(rr.entries),
            "per_source_counts": rr.per_source_counts,
            "errors": rr.errors,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        log.info("RSS: %d entries from %d feeds", len(rr.entries), len(rr.per_source_counts))
    else:
        log.info("Skipping RSS.")

    # EDGAR --------------------------------------------------------------
    if not args.skip_edgar:
        log.info("Fetching EDGAR filings ...")
        er = edgar_src.fetch(tickers, days_back=60, max_per_ticker=4)
        discovered.extend(er.entries)
        meta["sources"]["edgar"] = {
            "entries": len(er.entries),
            "errors": er.errors,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        log.info("EDGAR: %d filings, %d ticker errors", len(er.entries), len(er.errors))
    else:
        log.info("Skipping EDGAR.")

    # Tag + merge signals -------------------------------------------------
    existing = _load_json(DATA / "signals.json", [])
    curated_only = [s for s in existing if not s["id"].startswith(("rss-", "edgar-"))]
    if not curated_only:
        curated_only = seed.SIGNALS

    if args.skip_rss and args.skip_edgar:
        # Preserve previously-discovered entries so partial refreshes don't wipe.
        prev_discovered = [s for s in existing if s["id"].startswith(("rss-", "edgar-"))]
        merged = transform.merge(curated_only, prev_discovered)
        log.info("Skipped both RSS and EDGAR — preserving %d discovered signals.", len(prev_discovered))
        kept_count = len(prev_discovered)
    else:
        log.info("Tagging %d discovered signals ...", len(discovered))
        transform.tag(discovered, players)
        relevant = [s for s in discovered if s.get("layer_ids")]
        log.info("Kept %d / %d signals after tagging", len(relevant), len(discovered))
        merged = transform.merge(curated_only, relevant)
        kept_count = len(relevant)

    merged = merged[:500]
    _write_json(DATA / "signals.json", merged)

    meta["signals"] = {
        "curated": len(curated_only),
        "discovered_kept": kept_count,
        "total": len(merged),
    }
    _write_json(DATA / "meta.json", meta)

    log.info("Refresh done. Signals: %d (%d curated + %d discovered).", len(merged), len(curated_only), len(relevant))
    return 0


if __name__ == "__main__":
    sys.exit(main())
