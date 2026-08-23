---
name: run-inference-dashboard
description: Run, serve, launch, screenshot, or smoke-test the Inference Stack Dashboard. Use when asked to start the dashboard, verify the site renders, confirm a front-end change works in a real browser, screenshot the layer/movers pages, or check that the daily data refresh didn't break any page. Drives headless Chrome over every page and asserts each rendered its data.
---

# Run the Inference Stack Dashboard

Every page renders client-side: the browser fetches `data/*.json` and builds the DOM in JS. A curl of the JSON proves the data exists, not that the page renders it — so "does it work?" is a question only a real browser answers.

## Smoke harness (the agent path)

```bash
uv run .claude/skills/run-inference-dashboard/smoke.py
```

Serves the repo on an ephemeral port, drives headless Chrome through every page, waits for post-render markers, asserts each page rendered its data, does one real interaction, screenshots everything, exits non-zero on any failure. Takes about a minute. Needs `uv` and Google Chrome in `/Applications`; nothing else — the driver declares Playwright in a PEP 723 header and drives system Chrome (`channel="chrome"`), so there is no `playwright install` step and nothing lands in `pyproject.toml`.

Screenshots go to `screenshots/` beside the driver (gitignored, `*.FAIL.png` on error). **Look at them.** A page can pass every assertion and still look wrong.

Run it after `uv run python -m jobs.refresh` too: it is the render gate that catches a data-schema drift which committed clean JSON but broke a page.

To cover a different page or ticker, edit `PAGES` at the top of `smoke.py`. The `ready` selector must be one that exists only after the client-side render (`#content:not(.hidden)`, `#players-body tr`), never a static element, or the screenshot fires before the data paints.

## Human path

`uv run python -m http.server 8000`, then open the port. Editing JS or CSS: append `?v=N` or hard-reload, the static server sends no cache-busting headers.

## Gotchas

- **Wait for render, not load.** Pages `await loadAll()` then inject DOM; `domcontentloaded` returns before anything is on screen.
- **Period-toggle values are `ret_*`, not labels** — `data-period="ret_1d|ret_1w|ret_1m|ret_3m|ret_6m|ret_1y"`. The live one carries `.active`.
- **The site has no favicon**, so Chrome logs a console error on every page. The driver ignores `"Failed to load resource"` lines and catches real asset 404s through a separate response listener filtered to `.json`/`.js`/`.css`. Loosen that filter and every page false-fails.
- **Everything is CDN** (Tailwind, Alpine, ECharts, marked), so a CDN outage degrades pages with no Python error. The console capture here is the only detector. The Tailwind production nag is filtered out.
- **ECharts in a hidden container renders 0x0** unless `resize()` fires after un-hide. The driver settles 250 ms before screenshotting for this reason; a blank chart in a screenshot is this.
- **Chips inside layer cards must be `<span>`, not `<a>`.** Browsers hoist a nested `<a>` out of its parent and break the card layout.

## When it fails

| Symptom | Cause |
|---|---|
| chrome channel error / `ms-playwright` | System Chrome missing. On Linux or CI: `uv run --with playwright playwright install chromium` and drop the `channel` arg (untested here). |
| a movers page reports 0 rows | That day's `data/{us,tw}_movers.json` is stale or empty because a universe stage failed. Check `data/meta.json`, re-run the stage. |
| `stock-tsm` fails | `TSM` is not in `data/players.json`. Point it at a ticker that is. |
