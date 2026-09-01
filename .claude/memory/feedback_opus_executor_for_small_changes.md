---
name: feedback_opus_executor_for_small_changes
description: "Small, already-specced changes go to a single Opus executor, never a Fable sub-orchestrator with helpers"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0ecc8422-7379-4544-8301-c1155344c5a0
  modified: 2026-08-18T02:57:26.980Z
---

Alex, 2026-08-18: "use opus executor for these small changes going forward."

The trigger he corrected twice in one session: reaching for a Fable sub-orchestrator plus helpers for a change that is one condition in one file, a comment, and a test. Also for spawning a stand-in reviewer on a small CI change whose failure mode was only "merges stop working".

**Why:** the dispatch skill already says a job small enough to want zero helpers was never a sub-orchestrator job. The failure was not a missing rule but a missing check. Orchestration costs more and puts a planning layer between the hub and the work for no gain when the spec is already written.

**How to apply:** before dispatching, ask whether the brief already contains the spec. If it does, there is nothing to orchestrate — send it to one Opus executor with `no helpers` stated. Reserve Fable for work that genuinely needs decomposing across files, sources, or projects. "This touches production" is not by itself a reason to orchestrate; judge by whether the work needs planning, not by how scary the target is.

Related: [[feedback_claude_subagents_over_third_party_apis]]
