---
name: run-inference-dashboard
description: Run, serve, launch, screenshot, or smoke-test the Inference Stack Dashboard. Use when asked to start the dashboard, verify the site renders, confirm a front-end change works in a real browser, screenshot the layer/movers pages, or check that the daily data refresh didn't break any page. Drives headless Chrome over every page and asserts each rendered its data.
---

# Run the Inference Stack Dashboard

A static site (HTML + `data/*.json` + a Python data layer) with **no build step**.
Every page renders **client-side**: the browser fetches `data/*.json` and builds the
DOM in JS. So "does it work?" is a question only a real browser answers — a `curl` of
the JSON proves the data exists, not that the page renders it.

The driver is **`.claude/skills/run-inference-dashboard/smoke.py`**: it serves the repo
on an ephemeral port, drives headless Google Chrome through all 9 pages, **waits for the
post-fetch render markers** (not just page load), asserts each rendered its data (row
counts, heat-map cells, the ECharts quadrant), does one real interaction (the us-movers
period toggle), screenshots every page, and exits non-zero on any failure.

> Paths below are relative to the repo root (`/Users/alex/alexthegreat/Inference-Dashboard`).

## Prerequisites

- **uv** (project is uv-managed) and **Google Chrome** installed at `/Applications/Google Chrome.app`.
- That's it. The driver declares its own dep (Playwright) via a PEP 723 header, so
  `uv run` installs it into an ephemeral env on first run — nothing is added to
  `pyproject.toml`/`uv.lock`. It drives the **system Chrome** (`channel="chrome"`), so
  there is **no `playwright install` browser download**.

## Run (agent path) — the smoke harness

One command. Renders every page, verifies it, screenshots it:

```bash
uv run .claude/skills/run-inference-dashboard/smoke.py
```

Expected tail on success (takes ~45s; first run adds ~5s to fetch Playwright):

```
PAGE             RESULT
------------------------------------------------------------
index            pass
us-movers        pass
tw-movers        pass
signals          pass
stocks           pass
about            pass
layer-gpu        pass
stock-tsm        pass
architecture     pass
------------------------------------------------------------
screenshots -> .../run-inference-dashboard/screenshots
ALL PASS
```

Screenshots land in `.claude/skills/run-inference-dashboard/screenshots/` (gitignored;
`*.FAIL.png` for any page that errored). **Look at them** — a page can pass shallow checks
and still look wrong. View e.g. `screenshots/index.png`, `screenshots/layer-gpu.png`.

On failure the harness prints the specific problem per page (missing rows, a console
error, a failed JSON load, or a timeout) and exits 1 — so it doubles as a **post-refresh
render gate**: run it after `uv run python -m jobs.refresh` to catch a data-schema drift
that committed clean JSON but broke a page.

### Driving a different page / ticker

Edit the `PAGES` list at the top of `smoke.py`. Each entry is
`Page(name, url_path, ready_selector, asserts=[(selector, min_count)], interact=fn)`.
`ready` must be a selector that exists **only after** the client-side render (e.g.
`#content:not(.hidden)`, `#players-body tr`), not a static element — otherwise the
screenshot fires before the data paints. Parameterized pages take query strings
(`/layer.html?id=gpu`, `/stock.html?ticker=TSM`).

## Run (human path)

To click around yourself:

```bash
uv run python -m http.server 8000
```

Then open `http://localhost:8000/`. Ctrl-C to stop. (When editing JS/CSS, append `?v=N`
or hard-reload — the static server sets no cache-busting headers.)

## Gotchas

- **Wait for render, not load.** Pages `await loadAll()` then inject DOM. `wait_until=
  "domcontentloaded"` returns before any data is on screen; you must additionally wait
  for a post-render selector. This is why the driver keys off `#layers > *`,
  `#content:not(.hidden)`, `#players-body tr`, etc.
- **Period-toggle values are `ret_*`, not labels.** The us-movers/tw-movers window
  buttons are `data-period="ret_1d|ret_1w|ret_1m|ret_3m|ret_6m|ret_1y"` — not `"1W"`.
  The active one gets class `.active`.
- **The site has no favicon.** Chrome logs a `404 Failed to load resource` *console
  error* for `/favicon.ico` on every page. The driver ignores console lines containing
  `"Failed to load resource"` (real asset 404s are caught precisely by a separate
  response listener filtered to `.json`/`.js`/`.css`) — otherwise every page false-fails.
- **Tailwind CDN nag.** `cdn.tailwindcss.com should not be used in production` is a
  console warning, filtered out. Everything is via CDN (Tailwind/Alpine/ECharts/marked),
  so a CDN outage degrades pages with **no Python error** — the console/response capture
  here is the smoke detector for that.
- **ECharts in hidden containers** render 0×0 unless `resize()` fires after un-hide. The
  driver screenshots full-page after a 250 ms settle so the layer-page quadrant chart is
  captured; if a chart ever shows blank, that's the cause.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Executable doesn't exist … ms-playwright` or chrome channel error | System Chrome not found. Confirm `/Applications/Google Chrome.app` exists. To run without system Chrome (e.g. CI/Linux), `uv run --with playwright playwright install chromium` and change `channel="chrome"` → drop the arg in `smoke.py`. (Untested on Linux here.) |
| A movers page fails with 0 rows | The day's `data/{us,tw}_movers.json` is stale/empty (a universe stage failed). Check `data/meta.json` and re-run that stage. |
| `stock-tsm` fails | `TSM` not in `data/players.json` — pick any ticker that is (`MU`, `NVDA`, `INTC`). |
| Port already in use | N/A — the driver binds an ephemeral port itself; nothing to free. |
