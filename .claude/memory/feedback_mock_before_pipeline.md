---
name: feedback_mock_before_pipeline
description: "For front-end / 'show me the result' asks, build a shape-matching mock of the output FIRST and confirm it, before wiring the full pipeline"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1d009b0a-f547-4527-a83f-e55459326c69
---

When the deliverable is a front end or a "show me the result" ask, build a shape-matching mock of the output **first** and confirm it matches what Alex pictures — then wire the full pipeline. The expensive part is the plumbing; don't build it against a guessed output shape.

**Why:** An entire Datasette evaluation phase (install, canned queries, config) was thrown out because it shipped a raw record dump instead of the category×month pivot Alex actually wanted (2026-06-22). All that work was wasted on the wrong shape. The fix pattern — 3 quick prototypes rendered from live data, pick one, then build — was independently rediscovered two sessions later, so codify it rather than re-learn it.

**How to apply:**
- Before any pipeline work, mock the final output shape (2–3 variants from real data beats one) and get Alex to point at the one he means.
- Confirm the shape, not the styling — the pivot layout, the columns, the grouping — that's what plumbing depends on.
- Only then wire ingestion, config, and the full data path. Relates to [[feedback_content_before_polish]].
