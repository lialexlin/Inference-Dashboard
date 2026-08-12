---
name: reference-transcripts-source
description: "Earnings-call transcripts come from earningscalls.dev (free, US + ADRs); 16 local non-US tickers documented as gaps with no ADR mapping yet."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5951e414-dcbe-462f-9e74-7dfdec6e9383
---

Earnings-call and shareholder/analyst-call transcripts for the Inference-Dashboard live at:

- **Source**: earningscalls.dev (free, Nasdaq-fed, no signup, no paywall)
- **URL pattern**: `https://earningscalls.dev/transcripts/{TICKER}` 302-redirects to `/transcript/{call_id}`
- **Coverage on 2026-05-13**: 48 / 65 players (74%) — all US-listed including TSM/ASML/ASX ADRs
- **Storage**: `data/transcripts/{ticker}-{call_id}.json` (per-call, immutable once written, segmented by speaker+role) + `data/transcripts_index.json` (per-ticker pointers rebuilt each run)
- **Pacing**: 2.5s between requests; aggressive 429 after ~20 rapid requests, single retry with exponential backoff

**Gaps (16 unmapped local tickers, no ADR on earningscalls.dev):**
KR: 000660.KS (SK Hynix), 005930.KS (Samsung) · JP: 8035.T (TEL), 4062.T (Ibiden), 6967.T (Shinko) · CN: 300308.SZ (InnoLight), 300502.SZ (Eoptolink) · TW small caps: 2449.TW, 2345.TW, 3017.TW, 3653.TW, 3324.TWO, 3037.TW, 8046.TW · EU: SU.PA (Schneider), ATS.VI (AT&S) · Errors: SIEGY (Siemens, not on the platform)

**For non-US gaps**, the canonical fallbacks (NOT yet wired) are:
- **TSMC**: `investor.tsmc.com/english/quarterly-results/{YYYY}/q{N}` — links a `TSMC {Q}{YY} Transcript.pdf` directly (scraped via PDF text extraction; URL hash discoverable from the index page)
- **SK Hynix**: `news.skhynix.com/q{N}-{YYYY}-business-results/` — substantive press release with paraphrased mgmt commentary on supply/demand/capex, NOT a full transcript (no full Q&A in English)
- **Samsung**: similar press-release pattern, no full transcript
- **Quartr.com** would close most of the rest but their URLs aren't scraping-friendly and the API is ~$200/mo

Call types captured include "Earnings Call", "Shareholder/Analyst Call", "Analyst/Investor Day", and sell-side conference presentations ("Presents at Morgan Stanley TMT"). All are useful for narrative-drift tracking on supply/demand/capex; only filter by type if a specific job needs it.

See [[project-inference-dashboard]] for project context.
