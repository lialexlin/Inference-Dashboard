# Inference Dashboard

What it is, how to run it, what is out of scope: `README.md`. Rules below bind any session here, whatever the task.

- `data/*.json` is generated — never hand-edit. Two files in it are user-curated and must survive any regeneration: `data/manual_estimates.json`, `data/exit_triggers_manual.json`.
- `data/transcripts/*.json` is immutable once written. `call_id` is the upstream provider's key, so a rewrite means the provider changed, not that we should overwrite.
- The curated stack — layers, players, signals — is authored in `jobs/seed.py` and nowhere else.
- A curated signal `id` must never start with `rss-` or `edgar-`. That prefix check is the only thing keeping curated signals alive across refreshes.
- Every page renders client-side, so a front-end change is verified in a real browser, never by curl-ing the JSON. Skill: `run-inference-dashboard`.
- Industry labels are plain functional terms under an AI lens — not GICS, not AI buzzwords. Settled 2026-06-08 against both alternatives; don't relitigate.
- Paid data sources (transcripts, SemiAnalysis Core, EOD Historical) are deferred by decision, not by oversight.

Data-layer work — adding a layer, player, signal or feed, refresh semantics, which field comes from which source: skill `dashboard-data`.
