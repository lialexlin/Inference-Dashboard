---
name: feedback_visual_verification
description: "Before declaring ANY artifact done, exercise it from the consumer's vantage (render charts, check pipeline payloads, fresh-agent read-path) — and state scope limits proactively"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 49271799-db71-4e9e-8bd2-ada6f3a2584a
---

When I screenshot a rendered visual to "verify before saying it's done," I must judge it against the chart's *purpose*, not describe what's on screen in the most favorable light. On the market-euphoria Asia trajectory chart I rendered the Jan-2026 IPOs as disconnected dots, saw an unreadable confetti cloud (~20+ overlapping points per name spanning 40x→250x), and called it "IPO dots top-right" — rationalizing a real defect as done. Alex caught it: "why are there plot dots here? verify what you built visually before you say it's done."

Root cause was also a wrong premise: I labeled the IPOs "no history to trend," but each had ~5 months of *weekly* data (20+ points) — a trajectory, not a point. Fix: plot every name as a line (stubs as short dotted lines + small markers), not scatter dots.

**Why:** A screenshot only verifies if I actually evaluate readability/correctness against intent. Narrating a flattering interpretation is worse than not looking — it launders a defect as confirmed.

**How to apply:** After rendering, ask "does this achieve what the chart is *for*?" not "can I describe this positively?" If elements overlap into noise, if a label is missing, if a premise ("no history") contradicts the data, name it and fix it before declaring done. Relates to [[feedback_content_before_polish]] and [[feedback_self_contained_html]].

**Generalizes beyond charts — before declaring ANY artifact done, exercise it from the consumer's vantage:**
- **Charts** — render and scrutinize against the chart's purpose (above).
- **Data pipelines** — check the actual payload, not just the shape. A feed run was declared "fully validated" on queue shape while all 45 article bodies were empty. Count and read the content, not the record count.
- **Docs / workflows** — do a fresh-agent read-path test. A task dashboard pointed agents at a file that only renders in Obsidian's GUI — useless to the agent it was meant to serve. Read it the way its consumer will.

**State scope limits proactively at the "done" claim** — say what was NOT covered (which cases, which files, what wasn't tested) instead of waiting to be probed. 4+ violations of this rule in 2 weeks, all at the moment of the "done" claim.
