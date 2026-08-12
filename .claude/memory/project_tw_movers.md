---
name: project_tw_movers
description: TW listed-universe momentum radar (tw-movers.html + jobs/sources/tw_universe.py) — built 2026-06-01; verified-live API endpoints and two pending data gaps.
metadata: 
  node_type: memory
  type: project
  originSessionId: 4a506290-ba89-432f-9d44-3e10b4c88410
---

`tw-movers.html` + `jobs/sources/tw_universe.py` → `data/tw_movers.json`: a wave-1 momentum radar over the **entire** Taiwan listed universe (~1,900 TWSE+TPEx commons), not just the 66 tracked players. Sector "wave map" (median returns, robust to outliers) + sortable leaderboard, 1W/1M/3M/6M/YTD/1Y. Serves the user's wave-1→wave-2 supply-chain rotation thesis (see [[project_investment_framework]]). Part of [[project_inference_dashboard]].

**Verified-live data approach (probed 2026-06-01, no API key needed):** efficient reference-date-snapshot method — ~16 calls total, NOT per-stock.
- TWSE 上市 close per date: `GET www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=YYYYMMDD&type=ALLBUT0999&response=json` (Gregorian date; non-trading day → Chinese "no data" string → walk back). Stock table = the `.tables[]` entry with most rows; close at field idx 8.
- TPEx 上櫃 close per date: legacy `www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d=ROC/MM/DD&se=EW` (ROC year = Gregorian−1911; modern rwd path 302-redirects). Close at idx 2.
- Industry: TWSE `openapi.twse.com.tw/v1/opendata/t187ap03_L`; TPEx `www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O` (`SecuritiesIndustryCode`). Both also carry issued shares (`已發行普通股數` / `IssueShares`) → market cap. Common-stock filter `^[1-9]\d{3}$`.

**Granular sub-industry + market cap + size floor (DONE 2026-06-01):** official 2-digit sector is too coarse, so `tw_universe.py` has a hand-curated `SUBINDUSTRY` map (~280 codes, ~38 sub-industries) overriding the bucket — 旺宏→Memory, 臻鼎→PCB, 禾伸堂→Passive, plus Foundry/IC Design/ASIC&IP/OSAT/Test&Probe/Compound Semi/Lead Frame/Substrate/CCL/Cooling/Battery Pack/Display/Optical-Lens/LED/Networking/Server/Industrial PC/EMS/Robotics/IC Distribution/Telecom/Solar/Fab Engineering… `mktcap` = issued shares × close (100% both exchanges); sortable `Mkt Cap` column + **min-cap floor** control (default ≥NT$30B≈US$1B). The **wave-map recomputes medians client-side over the floored set** (`computeSectors`/`heatmapSubset`), so the coarse Semiconductor/Electronic-Components cards vanish at the floor. **Coverage invariant:** every name ≥~NT$28B is curated → 0 coarse-electronics labels at the default floor (Alex's hard ask). **Also fixed the old TPEx-"Other" gap** (reads the working TPEx host: ~880→43). **Gotcha hardened:** anchor dates require BOTH exchanges posted (Mon/after-close TPEx returns `stat=ok` 0-rows hours after TWSE; `_resolve_trading_day` walks back so TPEx isn't dropped).

**Maintenance + still-open:**
- As prices drift, names cross the NT$30B floor and may show a coarse-electronics label again → top up `SUBINDUSTRY` (find: coarse-elec codes ≥NT$30B not in the map). A research subagent fabricated ~5 wrong business IDs on the first 94-name pass (雍智/昇達科/亞光/AES-KY/etc.) — always web-verify the non-obvious ones, don't trust agent confidence.
- **Turnover filter** still optional (sharper liquidity gate than mktcap): capture 成交金額 (TWSE idx 4, TPEx idx 8). Not urgent now the size floor is the default.

Returns are raw closes — dividend/split/減資-unadjusted (caveat shown in UI; full fix needs adjusted prices, not in free TWSE feed).
