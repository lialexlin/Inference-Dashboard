"""Daily refresh orchestrator.

Pulls live data from all sources, tags signals, merges with curated seed data,
and atomically rewrites data/*.json.

Usage:
    python -m jobs.refresh                # full refresh
    python -m jobs.refresh --skip-rss     # for fast local iteration
    python -m jobs.refresh --skip-edgar
    python -m jobs.refresh --skip-ciq          # skip Capital IQ (e.g. when warehouse paused)
    python -m jobs.refresh --skip-tw-universe  # skip Taiwan universe momentum
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
from jobs import scoring
from jobs import bottleneck as bottleneck_stage
from jobs import cross_quarter_auto
from jobs import exit_triggers as exit_triggers_stage
from jobs.sources import prices as prices_src
from jobs.sources import rss as rss_src
from jobs.sources import edgar as edgar_src
from jobs.sources import capital_iq as ciq_src
from jobs.sources import openrouter as openrouter_src
from jobs.sources import transcripts as transcripts_src
from jobs.sources import transcripts_extract as transcripts_extract_src
from jobs.sources import tw_universe as tw_universe_src
from jobs import narrative as narrative_mod

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
    p.add_argument("--skip-scoring", action="store_true")
    p.add_argument("--skip-bottleneck", action="store_true")
    p.add_argument("--skip-openrouter", action="store_true")
    p.add_argument("--skip-exit-triggers", action="store_true")
    p.add_argument("--skip-transcripts", action="store_true")
    p.add_argument("--skip-narrative", action="store_true")
    p.add_argument("--skip-tw-universe", action="store_true")
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
        er = edgar_src.fetch(tickers, days_back=365, max_reports_per_ticker=2)

        # Attach summaries from data/filing_summaries.json (written by the
        # claude.ai daily routine). Missing summaries are fine — frontend
        # falls back to the bare card.
        summaries = _load_json(DATA / "filing_summaries.json", {})
        summarized = 0
        for entry in er.entries:
            summary = summaries.get(entry.get("accession"))
            if not summary:
                continue
            entry["summary"] = {
                "tldr": summary.get("tldr"),
                "takeaways": summary.get("takeaways", []),
                "guidance": summary.get("guidance"),
                "quote": summary.get("quote"),
                "quote_section": summary.get("quote_section"),
            }
            # LLM layer_tags override the keyword tagger for filings.
            llm_tags = summary.get("layer_tags") or []
            if llm_tags:
                entry["layer_ids"] = llm_tags
            # Surface the quote on the bare card too (legacy `quote` field).
            if summary.get("quote") and not entry.get("quote"):
                entry["quote"] = summary["quote"]
            summarized += 1

        discovered.extend(er.entries)
        meta["sources"]["edgar"] = {
            "entries": len(er.entries),
            "summarized": summarized,
            "errors": er.errors,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        log.info("EDGAR: %d filings (%d with summaries), %d ticker errors",
                 len(er.entries), summarized, len(er.errors))
    else:
        log.info("Skipping EDGAR.")

    # Transcripts --------------------------------------------------------
    # Earnings-call + shareholder-call transcripts from earningscalls.dev.
    # Per-call JSONs land in data/transcripts/{ticker}-{call_id}.json; the
    # aggregate index at data/transcripts_index.json is rebuilt every run
    # from on-disk files (cheap — counts a directory listing).
    if not args.skip_transcripts:
        log.info("Fetching transcripts for %d tickers ...", len(tickers))
        try:
            tr = transcripts_src.fetch(tickers, data_dir=DATA / "transcripts")
            index = transcripts_src.build_index(DATA / "transcripts")
            _write_json(DATA / "transcripts_index.json", index)
            meta["sources"]["transcripts"] = {
                "ok": index["tickers_covered"],
                "fetched_this_run": len(tr.fetched),
                "cached": len(tr.cached),
                "rate_limited": tr.rate_limited,
                "unmapped": tr.unmapped,
                "errors": tr.errors,
                "total_calls_on_disk": index["total_calls"],
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            log.info("Transcripts: %d new, %d cached, %d rate-limited, %d errors, %d total calls on disk",
                     len(tr.fetched), len(tr.cached), len(tr.rate_limited), len(tr.errors), index["total_calls"])
        except Exception as e:
            log.error("Transcripts stage failed: %s — preserving prior on-disk transcripts", e)
            meta["sources"]["transcripts"] = {
                "ok": 0,
                "errors": {"__stage__": str(e)},
                "ts": datetime.now(timezone.utc).isoformat(),
            }
    else:
        log.info("Skipping transcripts.")

    # Narrative theme extraction -----------------------------------------
    # Scan every transcript on disk and emit per-call tone scores across
    # supply / demand / capex / lead-times / pricing. Cheap (pure-Python
    # text scan), so we run it every refresh even if no new transcripts
    # landed — keeps the JSON consistent with on-disk transcripts.
    if not args.skip_narrative:
        log.info("Extracting narrative themes from on-disk transcripts ...")
        try:
            narrative = narrative_mod.compute(DATA / "transcripts")
            _write_json(DATA / "narrative_tracking.json", narrative)
            ns = narrative["summary"]
            meta["sources"]["narrative"] = {
                "ok": ns["tickers_covered"],
                "calls_analyzed": ns["calls_analyzed"],
                "total_mentions": ns["total_mentions"],
                "themes": ns["themes"],
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            log.info("Narrative: %d calls, %d tickers, %d theme mentions",
                     ns["calls_analyzed"], ns["tickers_covered"], ns["total_mentions"])
        except Exception as e:
            log.error("Narrative stage failed: %s — preserving prior narrative_tracking.json", e)
            meta["sources"]["narrative"] = {
                "ok": 0,
                "errors": {"__stage__": str(e)},
                "ts": datetime.now(timezone.utc).isoformat(),
            }
    else:
        log.info("Skipping narrative.")

    # Mine on-disk transcripts into signal entries so the bottleneck scorer and
    # exit-trigger pipeline see management Q&A language (not just filings + RSS).
    # Runs independently of the network fetch above — operates on cached JSONs —
    # so it works even when --skip-transcripts is set or the upstream is down.
    try:
        transcript_signals = transcripts_extract_src.build_signals(DATA / "transcripts")
        log.info("Transcripts → %d signal entries (supply/demand language present)",
                 len(transcript_signals))
        discovered.extend(transcript_signals)
    except Exception as e:
        log.error("Transcript extraction failed: %s", e)
        transcript_signals = []

    # Tag + merge signals -------------------------------------------------
    DISCOVERED_PREFIXES = ("rss-", "edgar-", "transcript-")
    existing = _load_json(DATA / "signals.json", [])
    curated_only = [s for s in existing if not s["id"].startswith(DISCOVERED_PREFIXES)]
    if not curated_only:
        curated_only = seed.SIGNALS

    if args.skip_rss and args.skip_edgar:
        # Preserve previously-discovered entries so partial refreshes don't wipe.
        # Freshly-mined transcript entries take precedence over their prior copy.
        new_transcript_ids = {s["id"] for s in transcript_signals}
        prev_discovered = [s for s in existing
                           if s["id"].startswith(DISCOVERED_PREFIXES)
                           and s["id"] not in new_transcript_ids]
        prev_discovered.extend(transcript_signals)
        # Re-tag so flags added in later code (e.g. arch_risk) get backfilled.
        transform.tag(prev_discovered + curated_only, players)
        merged = transform.merge(curated_only, prev_discovered)
        log.info("Skipped both RSS and EDGAR — preserving %d discovered signals (%d transcripts re-mined).",
                 len(prev_discovered), len(transcript_signals))
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

    # OpenRouter demand telemetry ----------------------------------------
    # Rolling daily snapshots of frontier inference token throughput.
    # Preserves prior history on parse failure (same shape as RSS/CIQ recovery).
    if not args.skip_openrouter:
        log.info("Fetching OpenRouter demand telemetry ...")
        prev_demand = _load_json(DATA / "demand_signals.json", {})
        prev_daily = prev_demand.get("daily", []) if isinstance(prev_demand, dict) else []
        try:
            demand = openrouter_src.fetch(existing=prev_daily)
            _write_json(DATA / "demand_signals.json", demand)
            latest = (demand.get("daily") or [])[-1] if demand.get("daily") else None
            meta["sources"]["openrouter"] = {
                "ok": 1 if latest else 0,
                "daily_rows": len(demand.get("daily") or []),
                "latest_date": latest["date"] if latest else None,
                "latest_total_tokens_b": latest["total_tokens_b"] if latest else None,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            log.info("OpenRouter: latest=%s, %d daily rows in history",
                     latest["date"] if latest else "?", len(demand.get("daily") or []))
        except Exception as e:
            log.error("OpenRouter stage failed: %s — preserving prior demand_signals.json", e)
            meta["sources"]["openrouter"] = {
                "ok": 0,
                "errors": {"__stage__": str(e)},
                "ts": datetime.now(timezone.utc).isoformat(),
            }
    else:
        log.info("Skipping OpenRouter.")

    # Cross-quarter auto-generator --------------------------------------
    # Derives supply-tightness shifts from filing_summaries for tickers
    # without a manually-written entry. Bottleneck (next stage) reads
    # cross_quarter.json fresh, so this must run before it.
    try:
        filing_summ_for_cq = _load_json(DATA / "filing_summaries.json", {})
        prev_cq = _load_json(DATA / "cross_quarter.json", {})
        manual_cq = {t: v for t, v in prev_cq.items() if not v.get("auto_generated")}
        cq = cross_quarter_auto.generate(filing_summ_for_cq, manual_cq)
        _write_json(DATA / "cross_quarter.json", cq)
        auto_count = sum(1 for v in cq.values() if v.get("auto_generated"))
        meta["sources"]["cross_quarter"] = {
            "ok": len(cq),
            "manual": len(manual_cq),
            "auto_generated": auto_count,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        log.info("Cross-quarter: %d entries (%d manual + %d auto)",
                 len(cq), len(manual_cq), auto_count)
    except Exception as e:
        log.error("Cross-quarter auto-gen failed: %s — preserving prior file", e)
        meta["sources"]["cross_quarter"] = {
            "ok": 0, "errors": {"__stage__": str(e)},
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    # Bottleneck heat-map ------------------------------------------------
    # Per-layer tightness score from signal density + supply-language extraction.
    # Reads merged signals, players, cross_quarter; emits data/bottleneck.json.
    if not args.skip_bottleneck:
        log.info("Computing per-layer bottleneck scores ...")
        try:
            cq_now = _load_json(DATA / "cross_quarter.json", {})
            bn = bottleneck_stage.compute(layers, merged, cq_now, players)
            _write_json(DATA / "bottleneck.json", bn)
            top3 = sorted(bn.items(), key=lambda kv: -kv[1]["tightness_score"])[:3]
            meta["sources"]["bottleneck"] = {
                "ok": len(bn),
                "top_layers": [
                    {"layer_id": lid, "tightness_score": v["tightness_score"]}
                    for lid, v in top3
                ],
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            log.info("Bottleneck: %d layers scored; top=%s",
                     len(bn), [f'{lid}={v["tightness_score"]}' for lid, v in top3])
        except Exception as e:
            log.error("Bottleneck stage failed: %s", e)
            meta["sources"]["bottleneck"] = {
                "ok": 0,
                "errors": {"__stage__": str(e)},
                "ts": datetime.now(timezone.utc).isoformat(),
            }
    else:
        log.info("Skipping bottleneck.")

    # Scoring ------------------------------------------------------------
    # Final stage: per-ticker business x valuation z-scores + per-layer auto status.
    # Reads everything written above. Idempotent and cheap (<1s for 66 tickers).
    if not args.skip_scoring:
        log.info("Computing per-ticker scores ...")
        try:
            manual = _load_json(DATA / "manual_estimates.json", {})
            fundamentals_now = _load_json(DATA / "fundamentals.json", {})
            prices_now = _load_json(DATA / "prices.json", {})
            history_now = _load_json(DATA / "multiples_history.json", {})
            scores, status_auto = scoring.compute(
                layers=layers,
                players=players,
                fundamentals=fundamentals_now,
                prices=prices_now,
                history=history_now,
                signals=merged,
                manual=manual,
            )
            scoring.write_outputs(
                scores=scores,
                layer_status_auto=status_auto,
                fund_path=DATA / "fundamentals.json",
                layers_path=DATA / "layers.json",
                scores_path=DATA / "scores.json",
                layers_data=layers,
                write_json=_write_json,
            )
            # Track coverage metrics for about page.
            manual_covered = sum(1 for t in [pp["ticker"] for pp in players]
                                 if t in manual and manual[t].get("fwd_eps_curr") is not None)
            quadrant_counts: dict[str, int] = {}
            component_coverage: dict[str, int] = {}
            for s in scores.values():
                quadrant_counts[s["quadrant"]] = quadrant_counts.get(s["quadrant"], 0) + 1
                for k in (s.get("components") or {}).keys():
                    component_coverage[k] = component_coverage.get(k, 0) + 1
            meta["sources"]["scoring"] = {
                "ok": len(scores),
                "quadrant_counts": quadrant_counts,
                "manual_estimates_coverage": manual_covered,
                "manual_estimates_total": len(players),
                "component_coverage": component_coverage,
                "tickers_scored": len(scores),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            log.info("Scoring: %d tickers, quadrants=%s, manual=%d/%d, components=%s",
                     len(scores), quadrant_counts, manual_covered, len(players),
                     component_coverage)
        except Exception as e:
            log.error("Scoring stage failed: %s", e)
            meta["sources"]["scoring"] = {
                "ok": 0,
                "errors": {"__stage__": str(e)},
                "ts": datetime.now(timezone.utc).isoformat(),
            }
    else:
        log.info("Skipping scoring.")

    # Exit-trigger status panel ------------------------------------------
    # Last stage: rolls up signals, demand_signals, filing_summaries, and the
    # manual Taiwan flag into 4 trigger states (green/amber/red).
    if not args.skip_exit_triggers:
        log.info("Computing exit-trigger states ...")
        try:
            demand_now = _load_json(DATA / "demand_signals.json", {})
            filing_summ_now = _load_json(DATA / "filing_summaries.json", {})
            taiwan_manual = _load_json(DATA / "exit_triggers_manual.json", {})
            triggers = exit_triggers_stage.compute(
                signals=merged,
                demand_signals=demand_now,
                filing_summaries=filing_summ_now,
                manual=taiwan_manual,
            )
            _write_json(DATA / "exit_triggers.json", triggers)
            meta["sources"]["exit_triggers"] = {
                "ok": 1,
                "overall": triggers["overall"],
                "states": {k: v["state"] for k, v in triggers["triggers"].items()},
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            log.info("Exit triggers: overall=%s, states=%s",
                     triggers["overall"], {k: v["state"] for k, v in triggers["triggers"].items()})
        except Exception as e:
            log.error("Exit-triggers stage failed: %s", e)
            meta["sources"]["exit_triggers"] = {
                "ok": 0,
                "errors": {"__stage__": str(e)},
                "ts": datetime.now(timezone.utc).isoformat(),
            }
    else:
        log.info("Skipping exit-triggers.")

    # Taiwan universe momentum -------------------------------------------
    # All-stock TWSE + TPEx daily closes, multi-window returns, sector medians.
    # Wave-1 detector: spot which sectors already ripped so the user can hunt
    # for Wave-2 laggards in the AI inference supply chain.
    # Runs LAST (slowest, most failure-prone network stage): a slow or failed
    # TW fetch must never delay or block the core dashboard stages above
    # (scoring / bottleneck / exit-triggers). Failure preserves the prior file.
    if not args.skip_tw_universe:
        log.info("Fetching Taiwan universe momentum ...")
        prev_movers = _load_json(DATA / "tw_movers.json", {})
        try:
            movers = tw_universe_src.fetch(existing=prev_movers)
            _write_json(DATA / "tw_movers.json", movers)
            meta["sources"]["tw_universe"] = {
                "ok": movers.get("count", 0),
                "stock_count": movers.get("count", 0),
                "sector_count": len(movers.get("sectors", [])),
                "latest_date": (movers.get("dates") or {}).get("latest"),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            log.info("TW Universe: %d stocks, %d sectors, latest=%s",
                     movers.get("count", 0),
                     len(movers.get("sectors", [])),
                     (movers.get("dates") or {}).get("latest"))
        except Exception as e:
            log.error("TW Universe stage failed: %s — preserving prior tw_movers.json", e)
            meta["sources"]["tw_universe"] = {
                "ok": 0,
                "errors": {"__stage__": str(e)},
                "ts": datetime.now(timezone.utc).isoformat(),
            }
    else:
        log.info("Skipping TW Universe.")

    _write_json(DATA / "meta.json", meta)

    log.info("Refresh done. Signals: %d (%d curated + %d discovered).", len(merged), len(curated_only), kept_count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
