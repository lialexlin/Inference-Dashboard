# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.40"]
# ///
"""
Render smoke-harness / driver for the Inference Stack Dashboard.

The dashboard is a static site whose every page renders CLIENT-SIDE: the
browser fetches data/*.json and builds the DOM with JS. So "does it work?"
is a question only a real browser can answer — a curl of the JSON proves the
data exists, not that the page renders it.

This driver:
  1. serves the repo root on an ephemeral port (its own threaded http.server),
  2. drives headless Google Chrome (Playwright, channel="chrome" — no browser
     download; reuses the Chrome already installed on the machine),
  3. visits every page, WAITS for the post-fetch render markers (not just load),
  4. asserts each page rendered its data (row counts, heat-map cells, …),
  5. captures console errors, uncaught page errors, and failed JSON/asset loads,
  6. performs one real interaction (us-movers period toggle) to prove the page
     is live, not a static snapshot,
  7. screenshots every page to ./screenshots/,
  8. prints a PASS/FAIL table and exits non-zero on any failure (CI-wirable).

Run:  uv run .claude/skills/run-inference-dashboard/smoke.py
"""
import functools
import http.server
import pathlib
import socket
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[3]          # repo root
SHOTS = pathlib.Path(__file__).resolve().parent / "screenshots"
SHOTS.mkdir(exist_ok=True)

# Console-error substrings that are noise, not failures.
IGNORE_CONSOLE = (
    "cdn.tailwindcss.com",            # Tailwind CDN's "don't use in prod" nag
    "favicon.ico",
    "Failed to load resource",        # resource 404s — caught precisely by the
                                      # response listener (filtered to data/assets),
                                      # so the generic console echo is just noise
                                      # (e.g. the favicon.ico the site has no icon for)
)
# Failed-response paths we care about (real data/assets, not favicon).
CARE_SUFFIX = (".json", ".js", ".css")


class Page:
    def __init__(self, name, path, ready, asserts=(), interact=None):
        self.name = name            # screenshot basename
        self.path = path            # url path incl. query
        self.ready = ready          # selector that only exists AFTER data render
        self.asserts = asserts      # list of (selector, min_count)
        self.interact = interact    # optional fn(page) -> None


def _click_period_1w(page):
    """Real interaction: flip the momentum window and confirm the table re-renders."""
    page.click('[data-period="ret_1w"]')
    page.wait_for_selector('[data-period="ret_1w"].active', timeout=10_000)
    page.wait_for_selector('#table-wrap table tbody tr', timeout=10_000)


PAGES = [
    Page("index", "/index.html", "#layers > *",
         asserts=[("#layers > *", 10), ("#exit-triggers > *", 1)]),
    Page("us-movers", "/us-movers.html", "#content:not(.hidden)",
         asserts=[("#heatmap .heatcell", 1), ("#table-wrap table tbody tr", 20)],
         interact=_click_period_1w),
    Page("tw-movers", "/tw-movers.html", "#content:not(.hidden)",
         asserts=[("#heatmap .heatcell", 1), ("#table-wrap table tbody tr", 20)]),
    Page("signals", "/signals.html", "#signals > *",
         asserts=[("#signals > *", 3)]),
    Page("stocks", "/stocks.html", "#groups section[data-group]",
         asserts=[("#groups section[data-group]", 1)]),
    Page("about", "/about.html", "#health-body tr",
         asserts=[("#health-body tr", 1)]),
    Page("layer-gpu", "/layer.html?id=gpu", "#players-body tr",
         asserts=[("#players-body tr", 1)]),
    Page("stock-tsm", "/stock.html?ticker=TSM", "#content > *",
         asserts=[("#content > *", 1)]),
    Page("architecture", "/architecture.html", "#header > *"),
]


def start_server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(ROOT))
    handler.log_message = lambda *a, **k: None          # silence access log
    # ephemeral port
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def check_page(browser, base, p):
    errors, failed = [], []
    page = browser.new_page(viewport={"width": 1440, "height": 1600})
    page.on("console", lambda m: (
        errors.append(m.text) if m.type == "error"
        and not any(s in m.text for s in IGNORE_CONSOLE) else None))
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("response", lambda r: (
        failed.append(f"{r.status} {r.url}") if r.status >= 400
        and r.url.endswith(CARE_SUFFIX) else None))

    problems = []
    try:
        page.goto(f"{base}{p.path}", wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_selector(p.ready, timeout=20_000)
        for sel, lo in p.asserts:
            n = page.locator(sel).count()
            if n < lo:
                problems.append(f"{sel}: got {n}, want >= {lo}")
        if p.interact:
            p.interact(page)
        page.wait_for_timeout(250)                       # let charts settle
        page.screenshot(path=str(SHOTS / f"{p.name}.png"), full_page=True)
    except Exception as e:
        problems.append(f"EXC {type(e).__name__}: {str(e).splitlines()[0]}")
        try:
            page.screenshot(path=str(SHOTS / f"{p.name}.FAIL.png"), full_page=True)
        except Exception:
            pass

    if errors:
        problems.append(f"{len(errors)} console error(s): {errors[0][:120]}")
    if failed:
        problems.append(f"{len(failed)} failed load(s): {failed[0]}")
    page.close()
    return problems


def main():
    httpd, port = start_server()
    base = f"http://127.0.0.1:{port}"
    print(f"serving {ROOT} at {base}\n")
    results = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        for p in PAGES:
            results[p.name] = check_page(browser, base, p)
        browser.close()
    httpd.shutdown()

    print(f"\n{'PAGE':<16} RESULT")
    print("-" * 60)
    ok = True
    for name, problems in results.items():
        if problems:
            ok = False
            print(f"{name:<16} FAIL")
            for pr in problems:
                print(f"{'':<16}   - {pr}")
        else:
            print(f"{name:<16} pass")
    print("-" * 60)
    print(f"screenshots -> {SHOTS}")
    print("ALL PASS" if ok else "FAILURES ABOVE")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
