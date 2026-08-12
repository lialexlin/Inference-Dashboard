---
name: claude-subagents-over-third-party-apis
description: "Processing work (extraction, summarization, analysis) defaults to Claude subagents, not third-party APIs like Gemini — cost routing, not a confidentiality rule"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: eedffcc6-6360-4068-a81f-005511df7ccd
  modified: 2026-07-23T03:44:33.114Z
---

Alex stopped a batch job mid-run (2026-07-23) that was calling the Gemini API for LPA terms extraction: "why would you send it to gemini??? why don't you use claude's subagent???? please stop it."

**Why:** Cost. Claude subagent capacity is already paid for; a third-party API adds per-token spend for work a subagent handles fine. (An earlier version of this memory framed it as a confidentiality rule — Alex corrected that; the objection was cost.)

**How to apply:** For extraction, summarization, analysis, or classification work, dispatch Claude subagents (model routing per global # Subagents). Reach for a non-Claude API only where an established workflow already uses one (currently: /pdf-to-md's Gemini conversion) or where Alex asks for it.
