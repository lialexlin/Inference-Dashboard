---
name: project_us_movers
description: US Movers page — US large-cap analogue of TW Movers; Nasdaq screener + yfinance bulk; default $50B floor; plain-industry grouping (NOT AI-thesis).
metadata: 
  node_type: memory
  type: project
  originSessionId: 83e53050-0a2c-4904-bbcd-5aeb6ec63bd3
---

US Movers (`us-movers.html` + `jobs/sources/us_universe.py` → `data/us_movers.json`) — built 2026-06-08 as the US-market analogue of [[project_tw_movers]]. Whole US large-cap universe wave-1 momentum radar: industry heat-map + sortable leaderboard, same UX as TW minus exchange filter / P/E / value-chain panel.

**Data path (cleaner than TW):** one Nasdaq screener call (`api.nasdaq.com/api/screener/stocks?...download=true`, needs a browser User-Agent) returns the whole ~7k universe with market cap; filtered at hard floor $10B (~970 names); only price *history* uses yfinance bulk `download(period="2y", auto_adjust=True)`, chunked. Closes are split+dividend-adjusted (unlike TW raw).

**Categorization — KEY nuanced feedback (Alex, 2026-06-08, took two iterations to land):** he wants the inference-stack names grouped at FUNCTIONAL granularity under the AI lens, with PLAIN labels — the sweet spot between two extremes he rejected: (1) over-AI buzzwords ("AI Accelerators / Neoclouds / Hyperscalers") — too much; (2) generic GICS ("Computer Hardware" buried SanDisk-memory and Dell-servers together) — too coarse. His words: "sandisk is memory and storage, dell is server… put them under the ai lens but don't over-ai it." Final design: **yfinance industry as the plain BASE** for the whole market (Nasdaq's own industry field is mislabelled junk — NextEra→"EDP Services"; yfinance gives Berkshire→Insurance, JPM→Banks) collapsed via `INDUSTRY_DISPLAY`, + `SYMBOL_OVERRIDE` = the **inference-stack functional overlay** (~80 names → Memory & Storage / Servers / GPUs & Accelerators / Custom Silicon / Foundry / Semiconductor Equipment / Networking / Optical Components / Cooling / Power & Grid / Nuclear / Cloud & Internet / Cloud Infrastructure …) + plain fixes (TSLA→EV, BTC miners). Classification static → cached in `data/us_industry.json` (cold start ~970 .info calls ~6-10 min; daily only fetches new names). Default leaderboard floor **≥$50B** (326 names); options $10B–$250B.

**Maintenance / watch-outs:** (1) yfinance-at-scale (~970 tickers, history + cold-cache .info) may be throttled from GitHub-Actions cloud IPs — graceful degradation preserves prior file; local residential run reliable. (2) Recent IPOs/spin-offs show inflated YTD/1Y (e.g. SNDK relisted Feb-2025) — flagged in page caveat, median wave-map absorbs. (3) To re-label a name, edit `INDUSTRY_DISPLAY`/`SYMBOL_OVERRIDE` or delete its `us_industry.json` entry. Stage runs dead-last in refresh after tw_universe. Part of [[project_inference_dashboard]].
