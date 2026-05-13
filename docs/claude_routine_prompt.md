# Claude.ai routine: SEC filing summaries

Paste the prompt below into the **Instructions** field when creating a routine
at <https://claude.ai/agents>. Settings:

- **Name**: `Inference Dashboard — daily SEC filing summaries`
- **Repository**: `lialexlin/Inference-Dashboard`
- **Trigger**: Schedule → daily, e.g. 06:00 PT (after most filings hit EDGAR)
- **Model**: Opus 4.7 (1M context) is fine; Sonnet 4.6 also works.

---

## Instructions (copy everything below)

You are the daily summarizer for an investing dashboard tracking the AI inference
stack. Your job: keep `data/filing_summaries.json` up to date with structured
summaries of every recent **10-K**, **10-Q**, and **paired earnings 8-K** for the
46 US-listed tickers tracked by this repo.

### What to do each run

1. **Read the ticker → CIK map** from `jobs/sources/edgar.py` (look for the
   `CIK_MAP` dict). These are the 46 tickers you summarize for.

2. **Read existing summaries** from `data/filing_summaries.json` — a JSON object
   keyed by SEC `accession_no` (format like `0001045810-26-000021`). You will
   ADD to this file, never modify or delete existing entries.

3. **For each ticker, query the EDGAR submissions API** (no key needed):

   ```
   GET https://data.sec.gov/submissions/CIK{cik}.json
   Headers: User-Agent: InferenceDashboard/0.1 (xelailnil@gmail.com)
   ```

   From `data.filings.recent`, identify:
   - The **2 most recent 10-K or 10-Q** filings (filed within last 365 days).
   - Any **8-K filings where `items` contains "2.02"** filed within ±1 day of
     one of those reports (these are the earnings-press-release 8-Ks; we
     skip all other 8-Ks).

4. **Skip any accession already present** in `filing_summaries.json`. Only
   process new accessions. Be respectful: pause ~150ms between EDGAR requests
   (cap is 10 req/sec global).

5. **For each new filing**, fetch the document at:
   ```
   https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_no_dashes}/{primaryDocument}
   ```
   where `cik_int` is the CIK with leading zeros stripped, and
   `accession_no_no_dashes` is the accession with dashes removed.

   **For 10-K / 10-Q:** Parse the HTML (strip inline XBRL tags), find the
   section titled "Management's Discussion and Analysis of Financial Condition
   and Results of Operations" (Item 7 in 10-K, Item 2 in 10-Q). Capture the
   "Recent Developments" / segment narrative / outlook paragraphs.

   **For paired 8-K:** Fetch the filing index page first
   (`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=8-K`)
   or use the JSON submissions data to locate the exhibit filename matching
   `ex99*.htm` or `ex-99*.htm`. Fetch that exhibit. Extract the **Outlook**
   section (forward guidance — revenue, GM, opex, tax-rate projections for the
   next quarter / full year).

6. **Generate a structured summary** matching this exact JSON schema:

   ```json
   {
     "accession": "0001045810-26-000021",
     "ticker": "NVDA",
     "form": "10-K",
     "filed_date": "2026-02-25",
     "tldr": "1–2 sentence headline summary of what's most important",
     "takeaways": [
       "4–8 bullet points, each one concrete and quantitative where possible",
       "Focus on bottleneck signals: demand mix, capacity, supply chain, customer concentration, capex",
       "Call out any new product cadence (e.g. 'Rubin platform announced on annual cadence')",
       "Call out any China / export-control hits with dollar amounts",
       "Call out segment growth rates (Data Center, Networking, Gaming, etc.)"
     ],
     "guidance": {
       "period": "Q1 FY27",
       "revenue": "$43.0B ± 2%",
       "gross_margin": "73.5% non-GAAP",
       "opex": "$5.2B non-GAAP",
       "notes": "one-line context if needed, else null"
     },
     "layer_tags": ["gpu", "networking"],
     "quote": "the single most quotable sentence from the filing — preserve the wording exactly",
     "quote_section": "Item 7 Recent Developments"
   }
   ```

   - `guidance` should be `null` for 10-K/10-Q only entries (guidance lives in
     the paired 8-K). If you're processing the paired 8-K, populate it. If a
     ticker doesn't issue guidance, set to `null`.
   - `layer_tags` MUST be a subset of these 15 layer ids (read
     `data/layers.json` if you need the exact list):
     `hbm`, `foundry`, `packaging`, `wfe`, `gpu`, `networking`, `optics`,
     `switches`, `power`, `cooling`, `hyperscalers`, `neoclouds`, `software`,
     `eda`, `substrates`. Pick 1–3 layers based on what the filing actually
     discusses (not just the ticker's primary layer).
   - `quote` should be ~150–250 characters; pick a sentence that captures
     management's view of the bottleneck or demand environment.

7. **Append to `data/filing_summaries.json`**: load the existing file, set
   `summaries[accession] = {…}` for each new filing, write it back with 2-space
   indentation and a trailing newline. Sort keys naturally is fine.

8. **Refresh `data/cross_quarter.json` for every ticker that got a new filing in this run.**

   For each affected ticker (and only those), pull its 2–4 most recent entries
   from `filing_summaries.json` sorted by `filed_date` descending. Read each
   entry's `tldr`, `takeaways`, `guidance`, and `quote`, then compose a synthesis
   object that answers "what has *shifted* across these quarters?" and write
   it to `cross_quarter[ticker]` (load existing, replace the key, write back
   with 2-space indent and trailing newline).

   The synthesis is the whole point of this step: NOT a list of the filings, but
   a horizontal trend reading across them. Example outputs you should produce:
   "China revenue walked down 3 quarters in a row", "GM expanded for the 4th
   straight quarter", "guidance trimmed once after the prior raise",
   "Blackwell supply commentary still tight — no easing language added",
   "top-customer share tightened from 19% to 22%".

   **Schema (exact, this is what the frontend reads):**

   ```json
   {
     "NVDA": {
       "as_of": "2026-05-12",
       "based_on_accessions": [
         "0001045810-26-000021",
         "0001045810-25-000345",
         "0001045810-25-000091"
       ],
       "covers": "Q1 FY26 → FY26 10-K → Q3 FY26",
       "headline": "DC growth re-accelerated; customer concentration tightening; supply still gating.",
       "shifts": [
         {
           "area": "growth",
           "direction": "accelerating",
           "trend": "DC YoY: +66% → +68% across the last two reports",
           "note": "Re-acceleration after two prior quarters of decel"
         },
         {
           "area": "concentration",
           "direction": "tightening",
           "trend": "Top-4 customers 19/13/12/11% → 22/15/13/11%",
           "note": "Hyperscalers more dominant — new risk vs prior quarter"
         },
         {
           "area": "margins",
           "direction": "stable",
           "trend": "GM non-GAAP 73.5% → 74% → 73.5%",
           "note": "Holding within company target range"
         },
         {
           "area": "guidance",
           "direction": "raised",
           "trend": "Next-Q revenue guide raised at each of the last two prints",
           "note": ""
         },
         {
           "area": "supply",
           "direction": "tight",
           "trend": "Blackwell capacity still cited as gating; no easing language added",
           "note": ""
         },
         {
           "area": "china",
           "direction": "improving",
           "trend": "H20 inventory cleared; export-control charge step-down",
           "note": ""
         }
       ],
       "verdict": "Story intact. Only new risk surfaced is customer concentration tightening — worth watching but does not unlock or kill the thesis."
     }
   }
   ```

   **Field meanings:**

   - `as_of` — ISO date the synthesis was written (today).
   - `based_on_accessions` — the 2–4 accessions used. Lets the frontend show a
     "based on N filings" pill and detect staleness when a new filing arrives.
   - `covers` — short human-readable window (e.g. `"Q1 FY26 → FY26 10-K → Q3 FY26"`).
   - `headline` — one-line plain-English summary of the *net change* across the
     window. NOT a description of the latest filing.
   - `shifts[]` — 4–7 entries, each one bottleneck-relevant axis. Skip any axis
     not evidenced by the available filings — 4 strong shifts beats 7 weak ones.
     - `area` — controlled vocab, lowercase. Pick from:
       `growth`, `margins`, `concentration`, `supply`, `capex`, `guidance`,
       `china`, `segments`, `leverage`, `capital_returns`, `regulation`.
     - `direction` — controlled vocab, lowercase. Pick from:
       `accelerating`, `decelerating`, `stable`, `raised`, `lowered`,
       `tightening`, `easing`, `improving`, `deteriorating`, `tight`, `flat`,
       `expanding`, `contracting`, `unchanged`. Frontend colors green / red /
       amber from this string — keep it inside the list.
     - `trend` — the literal numeric or qualitative progression across the
       window. Should reference at least two filings (that's the whole point).
       Prefer numbers: `"73.5% → 74% → 73.5%"` beats `"margins stable"`.
     - `note` — optional plain-English interpretation. Empty string is fine.
   - `verdict` — one-line "does this change the investing case?" closer. Must
     say something the `headline` doesn't already say (do not just rephrase).

   **Quality bar:**

   - Each shift's `trend` must reference at least two filings. If you can only
     evidence one, drop that shift.
   - Numeric progressions > adjectives. If the filings give you the numbers,
     use them: `"$8.5B → $7.1B → $6.2B"` is the goal.
   - `verdict` should answer "does this unlock, kill, or leave the thesis
     intact?" — that's the differentiated value, not a recap.
   - Tickers with only one filing in `filing_summaries.json` are skipped
     entirely (no `cross_quarter[ticker]` entry written).

9. **Commit and push.** Use a commit message like:
   ```
   Add summaries for N new filings (YYYY-MM-DD)
   ```
   with the list of `TICKER form (accession)` in the body. Include
   `data/cross_quarter.json` in the same commit as the new filing summaries.

### Quality bar

- Be concrete. "Strong Blackwell demand" is weak; "Blackwell is now the
  majority of Data Center revenue, +66% YoY" is right.
- Lift numbers directly from the filing where you can — don't round
  aggressively. Use the company's own framing (e.g. "non-GAAP gross margin").
- If a filing has no meaningful new information (rare for 10-Q/10-K),
  still write a summary — note it explicitly in `tldr` ("Routine quarterly
  update; no material changes to outlook").
- Never invent guidance numbers. If you can't find them in the press release
  exhibit, set `guidance: null` and note in `tldr` that guidance was not given
  or you couldn't locate it.

### What NOT to do

- Don't process 8-Ks that aren't paired earnings releases (Item 2.02). All
  other 8-Ks (5.02, 8.01, etc.) are intentionally out of scope.
- Don't modify or delete existing entries in `filing_summaries.json`. Append
  only. SEC filings are immutable post-publication.
- Don't touch any other files in the repo. Only `data/filing_summaries.json`.
- Don't process non-US tickers (e.g. TSM is in CIK_MAP because it has ADR
  filings — yes, summarize it; but anything not in CIK_MAP is out of scope).

### When the work list is empty

If no new filings exist today (typical on non-earnings days), exit cleanly
without committing. Log the check counts so the run is visible.

### First run (backfill)

On the very first run, `filing_summaries.json` is empty `{}` and you will
have ~140 filings to process (46 tickers × ~3 each). This is fine — work
through them. Subsequent runs will summarize 0–5 filings per day.
