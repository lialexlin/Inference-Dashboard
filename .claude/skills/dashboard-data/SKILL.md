---
name: dashboard-data
description: Change the Inference Dashboard's data layer — add a stack layer, a player ticker, a curated signal or an RSS feed; understand which field comes from yfinance vs Capital IQ and why; debug a refresh, a CI run, or an industry label. Use before editing anything under jobs/ or data/, and when a refresh or GitHub Actions run produced wrong or missing data.
---

# Dashboard data layer

Pipeline: `sources/* -> SQLite cache -> transform.py (tag) -> data/*.json (atomic) -> static HTML`.
The generated JSON is the contract; the frontend has no build step.

## Adding things

**A layer:** `LAYERS` and `LAYER_CONTENT` in `jobs/seed.py`, plus `LAYER_KEYWORDS` in `jobs/transform.py`. Re-run seed.

**A player ticker** — all four, in order:
1. `PLAYERS` in `jobs/seed.py`. Set `country`: it derives the CIQ reporting currency, and the ticker suffix does not. TSM and ASML are ADRs reporting in TWD and EUR.
2. US-listed → add `ticker -> CIK` to `CIK_MAP` in `jobs/sources/edgar.py`.
3. Seed with `--refresh-ciq-mapping`. On failure add `{ticker: companyId}` to `CIQ_OVERRIDES`, or `None` to skip; find the id with `find_company` in the `s&p` skill.
4. Refresh.

**A curated signal:** `SIGNALS` in `jobs/seed.py`. The `id` must not start with `rss-` or `edgar-` — reserved for discovered entries, and the prefix check is what preserves curated signals across refreshes.

**An RSS source:** a tuple in `FEEDS` in `jobs/sources/rss.py`.

## Refresh semantics

Partial refreshes merge rather than overwrite: `refresh.py` reads the previous `meta.json` and `signals.json`, so a skipped or failed stage keeps that stage's prior output, and a CIQ failure preserves the prior `ciq.*` blocks. Writes go `.json.tmp` then rename, so the frontend never sees half-written state. The two universe stages run dead-last because they are the slowest and most network-fragile; a failed TW/US fetch must never block core data.

## Which source, and why

| Field | Source | Why |
|---|---|---|
| Daily prices, 1m/6m/YTD | yfinance | CIQ has prices but is not daily-historical-friendly at scale |
| Forward P/E, target prices, analyst counts | yfinance | Axiom's CIQ Xpressfeed subscription excludes forward estimates |
| Next earnings date | yfinance | Reliable for US large caps and ADRs; spotty for Asian listings, which return `null` and render "—" |
| Trailing P/E, EV/EBITDA, P/S, P/B (current + 8y) | Capital IQ | Currency-aware, audit-grade, global; yfinance has only the current snapshot |
| Margins, growth, returns | Capital IQ | Pre-computed and globally consistent |
| Revenue / EBITDA / NI in USD | Capital IQ | Reporting currency from the PLAYERS `country` field |

CIQ creds live in `.env`, never committed; in CI they are repo secrets. Without them the stage logs `CIQ connect failed` and the run continues on prior values. Schema reference: the `s&p` skill.

## Industry labels

Plain functional terms under an AI lens: SanDisk is Memory & Storage, Dell is Servers. Alex rejected both alternatives on 2026-06-08 — generic GICS buried the thesis, AI buzzwords over-egged it.

Mechanically the base is yfinance sector/industry (the Nasdaq screener's own field is mislabelled — NextEra as "EDP Services", Visa and Alibaba as "Business Services"), collapsed through `INDUSTRY_DISPLAY`, with `SYMBOL_OVERRIDE` layering supply-chain names on top. To re-label: edit those two maps, or delete the symbol's entry in `data/us_industry.json` (a committed cache that keeps CI from cold-starting the slow yfinance `.info` fetch) to force a re-fetch.

TW works the same way: `SUBINDUSTRY` in `tw_universe.py` overrides the coarse official 2-digit sector. **Coverage invariant:** every TW name above roughly NT$28B is curated, so at the page's NT$30B default floor no coarse-electronics bucket should appear. Prices drift names across the floor — periodically top it up.

## Scoring

`business` and `valuation` z-scores are composed within the ticker's primary-layer peer set, not the whole universe. Quadrant cutoffs and the layer roll-up thresholds are constants at the top of `jobs/scoring.py`; `status_override` in `seed.py` pins a layer's label. EPS-revision scoring needs `fwd_eps_curr` plus at least one prior snapshot in `manual_estimates.json`; coverage is surfaced on `about.html`.

The numbers serve a bottleneck-rotation thesis: is inference demand actually growing (OpenRouter token throughput), which layer binds now (heat-map), how defensible is the choke point (business x valuation), what is already priced in (reverse-DCF, bisection at r=10% and terminal P/E 18), and what would end the trade (token growth, hyperscaler capex, architectural risk, Taiwan). Every signal carries an architectural-risk flag — Mamba, MoE, linear attention, KV-cache, distillation, BitNet — because those are the thesis-killers.

## Data gotchas

- **TW closes are dividend- and split-unadjusted**; US closes are adjusted. High-yield TW names show understated 1Y, and the two radars are not comparable on long windows. Intentional, matches how traders read the TWSE/TPEx tape.
- **TW anchor dates need both exchanges posted.** On lag days TPEx returns `stat=ok` with zero rows hours after TWSE has data; `_resolve_trading_day` walks back to the last day both have data. Without it ~880 TPEx names silently vanish.
- **The Nasdaq screener 403s without a browser User-Agent** (`SCREENER_HEADERS`).
- **yfinance can be throttled from CI.** The US universe bulk-downloads ~970 tickers and Yahoo blocks GitHub-Actions IPs; chunking plus per-batch try/except means partial failure drops names and total failure keeps the prior file. A collapsed US universe in CI is almost always this — the local run from a residential IP is reliable.
- **Recent IPOs and spin-offs show inflated 1Y** off a post-listing base. Correct arithmetic, flagged on the page, absorbed by the median-based wave map.
- **Some tickers legitimately have no price** — Shinko Electric (6967.T) is going private. CN A-shares work but lag.
- **Google News RSS proxies** intermittently return empty or rate-limited feeds; `about.html` surfaces the warning row.
- **pyenv blake2 noise** (`ERROR:root:code for hash blake2b was not found`) is harmless. Filter with `grep -v blake2`.

## Pushing after the cloud refresh

`.github/workflows/refresh.yml` runs the same `jobs.refresh` daily and commits `data/` as `inference-dashboard-bot`. Pushing from the laptop after the bot has pushed the same day rejects, and `git pull --rebase` conflicts on `data/meta.json` and `data/prices.json`. Local data is normally the superset, especially after a local CIQ run: `git checkout --theirs data/meta.json data/prices.json`, then `git rebase --continue`.
