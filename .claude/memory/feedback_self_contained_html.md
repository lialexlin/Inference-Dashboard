---
name: self-contained-html-artifacts
description: Internal artifacts default to a single self-contained HTML file; the generator code lives separately
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8e9983b4-0bca-4b47-99d0-6358c035c2c3
---

When the deliverable is a visual artifact to share internally (reports, dashboards, summaries), the output should be **one self-contained HTML file** — no server required to view, no external CSS/JS/font/image dependencies, no asset folder. A colleague opens the file by double-click and it just works (email, SharePoint, offline). The code that generates it can and should live separately (a script/module in the repo); only the rendered HTML travels.

**Why:** On the China VC revenue report (2026-06-26), the first build was wired as a FastAPI `/report` route requiring the dashboard server to run. Alex pushed back: "this needs server? so it's not a plain html page?" and set the principle — "most of the time these are just artifacts to be shared internally so should just be a single html file. the codes used to generate it can be separate, but the artifact should be a self-contained html page." A server route is fine as a *secondary* live view, but the shareable artifact must stand alone.

**How to apply:** Default any internal visual deliverable to a single self-contained `.html`. Use pure-CSS over JS chart libs where feasible; inline styles; avoid CDN `<link>`/`<script>`. Watch fonts — a Google Fonts `<link>` is an external dependency; name the brand fonts with a system fallback chain and drop the CDN link (system fonts are fine internally). Reserve base64-inlined brand fonts / fixed-layout PDF for external/LP-facing pieces (that's the `fund-one-pager` skill's job). Keep the generator (e.g. `Tools/china_vc_landscape/revenue_report.py`) in the repo; ship only the HTML. Related: [[feedback_content_before_polish]].
