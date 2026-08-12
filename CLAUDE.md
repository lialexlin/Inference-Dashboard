# Inference Stack Dashboard — orientation

A personal investing dashboard mapping the AI inference scaling stack across 15 layers, to spot which layers are still under-priced after the memory run-up. Two coupled views: a **stack overview** (layer cards with status and player chips) and a **live signals feed** (earnings/IR/filings/RSS commentary, layer-tagged), plus TW and US momentum radars.

## Architecture

Static HTML + JSON files + a Python data layer. **No build step, no framework** — the browser fetches `data/*.json` directly and Tailwind/Alpine/ECharts/marked all come from CDN.

```
sources/* → SQLite cache → transform.py (tag) → data/*.json (atomic) → static HTML
```

Deliberate: portable to GitHub Pages with no changes, no toolchain to maintain, easy to evolve by hand.

uv-managed. `uv sync` on a new machine; `launch.command` / `refresh.command` are the double-clickable wrappers.

## The files that carry rules

Everything else is readable from `ls` plus the file's own docstring. These four carry semantics you can't see:

- **`jobs/seed.py` is the source of truth for layers, players, and curated signals.** Add or edit the curated stack here, then re-run it. Also holds `CIQ_OVERRIDES` for tickers CIQ can't resolve, and `status_override` to pin a layer's label.
- **`data/*.json` is generated — never hand-edit.** Two exceptions, both user-curated: `data/manual_estimates.json` (forward EPS + revisions, refreshed post-earnings or monthly from Capital IQ / Bloomberg) and `data/exit_triggers_manual.json` (the Taiwan trigger state, toggled on geopolitical news).
- **`data/us_industry.json` is a committed classification cache** so CI never cold-starts the slow yfinance `.info` fetch. Delete a symbol's entry to force re-classification.
- **`data/transcripts/{ticker}-{call_id}.json` is immutable once written** — `call_id` is the upstream provider's stable key.

## How to add things

**A layer:** edit `LAYERS` and `LAYER_CONTENT` in `jobs/seed.py`, plus `LAYER_KEYWORDS` in `jobs/transform.py`. Re-run seed.

**A player ticker** — all four steps, in order:
1. Add to `PLAYERS` in `jobs/seed.py`. Set `country`, which is what derives the CIQ reporting currency.
2. If US-listed, add `ticker → CIK` to `CIK_MAP` in `jobs/sources/edgar.py`.
3. Run seed with `--refresh-ciq-mapping` to resolve against Capital IQ. On failure add `{ticker: companyId}` — or `None` to skip — to `CIQ_OVERRIDES`; find the id via `find_company` in the CIQ skill.
4. Run refresh.

**A curated signal:** edit `SIGNALS` in `jobs/seed.py`. The `id` must NOT start with `rss-` or `edgar-` — those prefixes are reserved for discovered entries, and that prefix check is the only thing keeping curated signals alive across refreshes.

**An RSS source:** add a tuple to `FEEDS` in `jobs/sources/rss.py`.

## Refresh model

- **Curated signals are durable**, preserved across refreshes by the id-prefix check above.
- **Partial refreshes don't wipe data.** `refresh.py` reads the previous `meta.json` and `signals.json` and merges, so skipping a stage never drops that stage's existing output. A CIQ failure preserves the prior `ciq.*` blocks.
- **Atomic JSON writes** (`.json.tmp` then rename) — the frontend never sees half-written state.
- **The two universe stages run dead-last** because they are the slowest and most network-failure-prone, so a slow or failed TW/US fetch never blocks core dashboard data.

## Cloud refresh (GitHub Actions)

`.github/workflows/refresh.yml` runs the same `jobs.refresh` daily on a GitHub-hosted runner, commits `data/` as `inference-dashboard-bot`, and Pages auto-redeploys on the push.

CIQ needs Snowflake creds as repo secrets (`SF_ACCOUNT`, `SF_USER`, `SF_PASS`). Without them the stage logs `CIQ connect failed`, preserves prior `ciq.*` blocks, and the run continues.

**Race-with-bot gotcha:** pushing from the laptop after the bot has pushed the same day rejects, and `git pull --rebase` then conflicts on `data/meta.json` / `data/prices.json`. Resolve with `git checkout --theirs data/meta.json data/prices.json` — local data is normally the superset, especially after a local CIQ run — then `git rebase --continue`.

## Data source split — and why

| Field | Source | Why |
|---|---|---|
| Daily prices, 1m/6m/YTD changes | yfinance | CIQ has prices but isn't daily-historical-friendly at scale |
| **Forward P/E, target prices, analyst counts** | yfinance | Axiom's CIQ Xpressfeed subscription doesn't include forward estimates |
| **Next earnings date** | yfinance | Reliable for US large caps + ADRs; spotty for Asian listings and a few US tickers, which return `null` and render "—" |
| **Trailing P/E, EV/EBITDA, P/S, P/B (current + 8y)** | S&P Capital IQ | Currency-aware, audit-grade, global. yfinance has only the current snapshot |
| **Margins, growth, returns** | S&P Capital IQ | Pre-computed and globally consistent |
| Revenue/EBITDA/NI in USD | S&P Capital IQ | Reporting currency comes from the PLAYERS `country` field, **NOT the ticker suffix** — TSM and ASML are ADRs reporting in TWD/EUR |

CIQ creds in `.env`, never committed. Schema reference: the `s&p` skill in the vault.

## Classification labels — a settled preference, don't relitigate

The US universe's industry labels are **plain functional terms under an AI lens**. Alex rejected both ends on 2026-06-08: generic GICS buried the thesis ("Computer Hardware" hid both SanDisk-memory and Dell-servers), and AI buzzwords over-egged it ("AI Accelerators", "Neoclouds", "Hyperscalers"). The instruction was *"put them under the ai lens but don't over-ai it."* So SanDisk is Memory & Storage and Dell is Servers.

Mechanically: the base reads **yfinance** sector/industry (the Nasdaq screener's field is mislabelled — NextEra as "EDP Services", Visa and Alibaba and Accenture all as "Business Services"), collapsed through `INDUSTRY_DISPLAY`; `SYMBOL_OVERRIDE` layers the inference-stack supply-chain names on top. To re-label, edit those two maps or delete the symbol's `us_industry.json` entry to force a re-fetch.

The same principle governs TW: `SUBINDUSTRY` in `tw_universe.py` is a hand-curated code→sub-industry map that overrides the coarse official 2-digit sector, so the wave-map resolves real feeder sub-sectors rather than a single "Electronic Components" blob.

**Coverage invariant:** every TW name above roughly NT$28B is curated, so at the page's default NT$30B floor no coarse-electronics bucket should appear. As prices drift, names cross the floor — periodically find coarse-electronics codes above the floor that aren't in `SUBINDUSTRY` and top it up.

## Scoring — Business × Valuation → quadrant

Each ticker gets a `business` and `valuation` z-score (positive = good), each composed from components z-scored **within the ticker's primary-layer peer set**, not the whole universe.

| business | valuation | label |
|---|---|---|
| > 0.3 | > 0.3 | **underappreciated** (top idea — strong growth, cheap) |
| > 0.3 | < −0.3 | **priced-in** (strong growth, already rallied) |
| < −0.3 | > 0.3 | **value-trap** (cheap, no growth) |
| < −0.3 | < −0.3 | **avoid** |
| else | else | **fair** |

Layer status rolls the player quadrants up: ≥30% underappreciated → underappreciated; ≥50% priced-in → priced-in; a spread distribution → mixed; else fairly-priced. `status_override` pins it when set. Thresholds live in the constants at the top of `jobs/scoring.py`.

**EPS-revision scoring needs at minimum `fwd_eps_curr` plus one prior snapshot** in `manual_estimates.json`. Coverage is surfaced on `about.html`.

## Framework view — Demand × Bottleneck × Moat × Exit

The dashboard operationalizes a Druckenmiller-style bottleneck-rotation thesis on inference scaling, through five primitives:

| Primitive | What it answers |
|---|---|
| **Demand telemetry** (OpenRouter token throughput) | Is inference demand actually growing — variant perception vs the tape |
| **Bottleneck heat-map** | Which layer binds *now* |
| **Choke-point moat** | The Business × Valuation score |
| **What's priced in** (reverse-DCF) | Implied 5y CAGR vs recent growth, bisection at r=10% and terminal P/E 18 |
| **Exit triggers** | Token growth, hyperscaler capex, architectural risk, Taiwan |
| **Architectural risk** | A thesis-killer flag on every signal (Mamba / MoE / linear attention / KV-cache / distillation / BitNet) |

## Known gotchas

- **Browser cache during dev** — append `?v=N` or hard-reload when editing JS/CSS. The static server sets no cache-busting headers.
- **Nested anchor tags** — chips inside layer cards must be `<span>`, not `<a>`. Browsers hoist a nested `<a>` out of its parent and break the layout.
- **Hidden ECharts containers** — call `chart.resize()` after un-hiding or the canvas stays 0×0.
- **pyenv blake2 noise** — `ERROR:root:code for hash blake2b was not found` on every Python startup is harmless. Filter with `grep -v blake2`.
- **TW closes are dividend- and split-unadjusted** (raw, not total-return), so high-yield names show understated 1Y. Intentional and documented on the page — it matches how traders read the TWSE/TPEx tape. **US closes ARE adjusted**, so the two radars are not directly comparable on long windows.
- **TW anchor dates need BOTH exchanges posted.** On data-lag days (Mondays, right after close) TPEx returns `stat=ok` with zero rows hours after TWSE has data. `_resolve_trading_day` walks back to the last day both exchanges have data — without it the ~880 TPEx names silently vanish.
- **The Nasdaq screener 403s without a browser User-Agent** (`SCREENER_HEADERS`).
- **yfinance at scale may be throttled from CI.** The US universe bulk-downloads ~970 tickers, far more aggressive than the core prices stage, and Yahoo can block GitHub-Actions IPs. Chunking plus per-batch try/except means partial failure just drops names and total failure preserves the prior file. A collapsed US universe in a CI run is almost always this; the local run from a residential IP is reliable.
- **Recent IPOs and spin-offs show inflated 1Y** off a post-listing base. Arithmetically correct, flagged in the page caveat, and the median-based wave-map absorbs it.
- **Some tickers legitimately have no price data** — Shinko Electric (6967.T) is being taken private by JIC, so its chip renders without a price. CN A-shares work but can lag; verify on the layer page.
- **Google News RSS proxies** occasionally return empty or rate-limited feeds. feedparser tolerates it and `about.html` surfaces the warning row.

## Scope decisions (settled)

- **Paid sources deferred to v2** (transcripts, SemiAnalysis Core, EOD Historical). Free coverage is ~85% of the signal value.
- **No portfolio tracking.** This is a research dashboard, not a brokerage UI. Out of scope by design.
- **Open design gap:** Co-Packaged Optics is in the keyword tagger so signals route correctly, but the Optics layer markdown still frames the thesis around pluggable transceivers only. Enriching it needs a "pluggable today, CPO tomorrow" axis plus CPO positioning on the relevant player roles.
