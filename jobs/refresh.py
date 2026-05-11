"""Daily refresh orchestrator.

Pulls live data from all sources, tags signals, merges with curated seed data,
and atomically rewrites data/*.json.

Usage:
    python -m jobs.refresh                # full refresh
    python -m jobs.refresh --skip-rss     # for fast local iteration
    python -m jobs.refresh --skip-edgar
    python -m jobs.refresh --skip-ciq     # skip Capital IQ (e.g. when warehouse paused)
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
from jobs.sources import capital_iq as ciq_src

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
    p.add_argument("--skip-ciq", action="store_true")
    p.add_argument("--tickers", help="comma-separated ticker subset for prices/edgar/ciq (debug)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,  # otherwise pyenv blake2 root-handler shadows our config
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

    # Capital IQ ----------------------------------------------------------
    # Run before yfinance: the heavy fundamentals + multiples come from CIQ
    # when available; yfinance fills the forward-data gap (forwardPE, target
    # prices) that CIQ's Xpressfeed subscription doesn't include.
    prev_fund = _load_json(DATA / "fundamentals.json", {})
    ciq_blocks: dict[str, dict] = {}
    ciq_history: dict[str, dict] = _load_json(DATA / "multiples_history.json", {})

    if not args.skip_ciq:
        ciq_mapping = _load_json(DATA / "ciq_mapping.json", {})
        if not ciq_mapping:
            log.warning("data/ciq_mapping.json missing — run `python -m jobs.seed --refresh-ciq-mapping` to enable CIQ stage. Skipping.")
        else:
            country = {p["ticker"]: p.get("country", "US") for p in players}
            cid_map = {t: v["company_id"] for t, v in ciq_mapping.items()
                       if t in tickers and v.get("company_id") is not None}
            currency_map = {t: ciq_src.COUNTRY_TO_CURRENCY.get(country.get(t, "US"), "USD")
                            for t in cid_map}
            log.info("Fetching CIQ for %d tickers (%d resolved) ...", len(tickers), len(cid_map))
            try:
                cr = ciq_src.fetch(list(cid_map.keys()), cid_map, currency_map)
                ciq_blocks = cr.snapshot
                # Merge new history into prior history (preserve unrefreshed tickers)
                ciq_history.update(cr.history)
                _write_json(DATA / "multiples_history.json", ciq_history)
                meta["sources"]["ciq"] = {
                    "ok": len(cr.snapshot),
                    "history_tickers": len(cr.history),
                    "errors": cr.errors,
                    "unmapped": [t for t in tickers if cid_map.get(t) is None],
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                log.info("CIQ: %d snapshots, %d histories, %d errors",
                         len(cr.snapshot), len(cr.history), len(cr.errors))
            except Exception as e:
                log.error("CIQ stage failed: %s — preserving prior fundamentals.json ciq blocks", e)
                meta["sources"]["ciq"] = {
                    "ok": 0, "history_tickers": 0,
                    "errors": {"__stage__": str(e)},
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                # Re-use prior CIQ blocks so the frontend doesn't lose data.
                ciq_blocks = {t: prev_fund[t]["ciq"] for t in prev_fund
                              if isinstance(prev_fund[t], dict) and prev_fund[t].get("ciq")}
    else:
        log.info("Skipping CIQ.")
        ciq_blocks = {t: prev_fund[t]["ciq"] for t in prev_fund
                      if isinstance(prev_fund[t], dict) and prev_fund[t].get("ciq")}

    # Prices + fundamentals -----------------------------------------------
    if not args.skip_prices:
        log.info("Fetching prices for %d tickers ...", len(tickers))
        pr = prices_src.fetch(tickers)
        _write_json(DATA / "prices.json", pr.prices)
        # Merge yfinance fundamentals with CIQ blocks under a `ciq` sub-key.
        merged_fund = dict(pr.fundamentals)
        for t, block in ciq_blocks.items():
            merged_fund.setdefault(t, {})["ciq"] = block
        _write_json(DATA / "fundamentals.json", merged_fund)
        meta["sources"]["prices"] = {
            "ok": len(pr.prices),
            "errors": pr.errors,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        log.info("Prices: %d ok, %d errors", len(pr.prices), len(pr.errors))
    else:
        log.info("Skipping prices.")
        # Even when prices skipped, refresh the ciq-merged fundamentals if CIQ ran.
        if ciq_blocks:
            for t, block in ciq_blocks.items():
                prev_fund.setdefault(t, {})["ciq"] = block
            _write_json(DATA / "fundamentals.json", prev_fund)

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

    log.info("Refresh done. Signals: %d (%d curated + %d discovered).", len(merged), len(curated_only), kept_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
