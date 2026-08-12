---
name: feedback_pull_before_data_analysis
description: "On Inference-Dashboard, git pull before any data-dependent analysis — the daily bot refreshes data/*.json, so a local clone goes stale fast."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 71924782-bbc9-40fb-a27c-a2989e14a90b
---

Before running any analysis that reads `data/*.json` on the [[project_inference_dashboard]], `git fetch origin && git pull` first (or at minimum check `data/meta.json` `last_refresh_at` vs today).

**Why:** The GitHub Actions bot (`inference-dashboard-bot`) commits a fresh daily refresh to `origin/main` every day (~22:00 UTC). A local clone falls behind within days. In one session I ran a 30-agent improvement-audit workflow against a 17-day-stale local clone and produced three confident "verified live defects" — a *dead daily cron*, the token-growth exit trigger *crying wolf RED*, and *13 past-dated earnings dates* — that were ALL stale-clone artifacts. On fresh data: cron healthy, overall=amber, 0 past-dated. Worse, the position-quadrant reads (e.g. "NVDA/ETN underappreciated, SK Hynix priced-in") were also stale and wrong (fresh: underappreciated bucket empty). Alex caught it.

**How to apply:** For data-dependent work here, pull first. Local has significant uncommitted WIP, so use stash-the-conflicting-data-files → `git pull --ff-only` → leave stash (the bot only touches `data/`, never code). Then re-verify any data-derived claim against the freshly-pulled files before stating it.
