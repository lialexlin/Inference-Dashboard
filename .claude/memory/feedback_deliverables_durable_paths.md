---
name: deliverables-durable-paths
description: "Session scratchpad is wiped on session resume — deliverables and reusable code must land in durable paths (vault Tools/, Temp/, deal folder), scratchpad only for true intermediates"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 485a8e16-506b-4fb0-8c20-0d80ee1a5ab7
---

The session scratchpad (`/private/tmp/claude-501/...`) is deleted when a session resumes. On 2026-07-06 a fully built + QA'd GP one-pager PPTX pipeline (generator, content JSON, output decks) lived only there and was lost when Alex asked "where is the ppt" after a session restart; the whole build had to be re-dispatched.

**Why:** The harness instruction "use scratchpad for temporary files" applies to intermediates. Anything Alex will open, or code that will be reused (a pipeline headed for a skill or Tools/), is not temporary — losing it costs a full rebuild cycle and credibility.

**How to apply:** Before ending any turn that produced a deliverable or reusable code, make sure it exists at a durable path: vault `Tools/` for shared code, the deal folder or `Temp/` for work products, `~/Downloads` for files Alex asked to open. Dispatch subagent build prompts with a durable working directory from the start, never the scratchpad. Related: [[readback-verification]].
