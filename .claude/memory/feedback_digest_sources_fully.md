---
name: feedback-digest-sources-fully
description: Data room / source extraction must read the full extent — never cap rows/columns/pages by guess; probe dimensions first
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 042e33b8-5f7d-4494-92b5-3a9db8f785df
---

When digesting data room or source material (xlsx, PDFs, converted md), read the full extent of the artifact. Never cap the read at a guessed width/depth (`max_col=8`, first N rows, first N pages) for output compactness — a header that happens to fill the cap makes truncation invisible, and conclusions drawn from the truncated view read as verified when they aren't.

**Why:** On HyT (2026-07-17) an LP tab was read with `max_col=8`; the sheet had 17 columns and the USD Fund II column sat at column 9. This produced a confident false negative ("no USD II column — the LP list was fabricated") delivered as a verification finding. Alex: "digest it fully — don't guess, this is very important."

**How to apply:**
- Probe dimensions first (`ws.max_column`/`ws.max_row`, page count, file length), then read everything within them. Compress the *output*, never the *read*.
- Any negative claim about a source ("the file doesn't contain X") requires a full-extent read of that file — same bar as [[reference_readback_verification]].
- Same family as [[feedback_excel_merged_cells]]: extraction conveniences that silently drop data.
