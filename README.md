# Inference Dashboard

Personal investing dashboard mapping the AI inference scaling stack — 15 layers, ~75 tickers, live bottleneck signals.

## Quick start (one click)

In Finder:
- **Double-click `launch.command`** → server starts and your browser opens to the dashboard.
- **Double-click `refresh.command`** → pulls the latest prices and signals (~30s).

Close the Terminal window (or Ctrl+C) to stop the server.

## Quick start (terminal)

```bash
pip install -e .
python -m jobs.seed       # one-time
python -m jobs.refresh    # daily — pulls live data
python -m http.server 8000
```

## Layout

| Path | What |
|---|---|
| `index.html` | Stack overview (15 layers + status badges + player chips) |
| `layer.html?id=optics` | Per-layer detail (markdown, players, signals) |
| `signals.html` | Chronological signal feed |
| `about.html` | Source health + last refresh |
| `data/*.json` | Generated data files (frontend reads these) |
| `content/layers/*.md` | Long-form per-layer copy |
| `jobs/seed.py` | Curated stack map + initial signals |
| `jobs/refresh.py` | Daily data pull orchestrator |
| `jobs/sources/*.py` | One module per upstream source |

## Refresh schedule

Manually: `python -m jobs.refresh`.

Daily via launchd (macOS): see `jobs/com.inference-dashboard.refresh.plist.example`.

## Cloud migration

Push repo → enable GitHub Pages → enable `.github/workflows/refresh.yml`. Same code, same JSON contract. Free.

## Out of scope

No portfolio tracking, no intraday prices, no auth, no backtests. Research dashboard, not brokerage UI.
