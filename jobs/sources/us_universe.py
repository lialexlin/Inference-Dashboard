"""US large-cap universe momentum — Nasdaq screener + yfinance bulk history.

The US analogue of jobs/sources/tw_universe.py. Same wave-1 detector idea —
show what has ALREADY moved across the US large-cap universe, grouped by
industry, so the investor can spot "Semiconductors ripped +30% but Networking
is flat" and go research the lagging cell for a wave-2 entry.

The data path is cleaner than the Taiwan one: market cap comes FREE from the
Nasdaq screener API in a single call. Price history needs yfinance (batched
download(), only for names above MIN_MKTCAP — bounded, not the whole 7k tape).

**Classification** is plain "what the company actually does" — NOT an AI-thesis
overlay. The Nasdaq screener's own industry field is a mislabelled mess (it
files NextEra Energy under "EDP Services", lumps Visa + Alibaba + Accenture into
"Business Services"), so instead we read yfinance's clean GICS-based
sector/industry (Apple → Consumer Electronics, Tesla → Auto, Berkshire →
Insurance, CRM → Software) and collapse its ~140 industries into ~50 readable
buckets via INDUSTRY_DISPLAY. Classification is STATIC, so it's cached in
data/us_industry.json and only fetched for symbols not already cached — the
daily job stays fast; the first run (cold cache) does ~970 .info calls (~6-10
min) once.

Schema of data/us_movers.json mirrors tw_movers.json:
{
  "as_of": "...", "dates": {...}, "count": N, "min_mktcap": 1e10,
  "stocks": [
    {"symbol","name","sector","industry","industry_en","close","mktcap",
     "pe":null,"ret_1d".."ret_1y","tracked"}
  ],
  "sectors": [ {"industry","industry_en","n","median_1d".."median_1y"} ]
}

Closes are yfinance split/dividend-adjusted (unlike the Taiwan page's raw
closes). Graceful degradation: any HTTP/parse failure raises so the refresh
caller preserves the prior us_movers.json.
"""
from __future__ import annotations

import json
import logging
import re
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

LOG = logging.getLogger(__name__)

TIMEOUT = 60
MIN_MKTCAP = 10e9          # hard fetch floor (~970 names); frontend floor defaults higher
BATCH = 120               # tickers per yfinance download() call
BATCH_SLEEP_S = 1.0       # politeness between yfinance batches
INFO_SLEEP_S = 0.05       # politeness between per-ticker .info classification calls
INFO_CHECKPOINT = 50      # persist the classification cache every N fetches
# Screener symbols: 1-5 letters, optionally a single share-class after "/".
SYMBOL_RE = re.compile(r"^[A-Z]{1,5}(/[A-Z])?$")

SCREENER_URL = (
    "https://api.nasdaq.com/api/screener/stocks"
    "?tableonly=true&limit=10000&offset=0&download=true"
)
SCREENER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Trailing share-class / instrument phrases stripped from screener names.
_NAME_SUFFIX_RE = re.compile(
    r"\s+(Common Stock|Common Shares|Ordinary Shares|"
    r"Class [A-Z] (Common Stock|Ordinary Shares|Capital Stock)|"
    r"American Depositary Shares|ADS|"
    r"\(.*?\)).*$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Display-label taxonomy.
# yfinance's industry strings are already clean and GICS-based; this collapses
# its ~140 industries into ~50 readable buckets so the heat-map isn't a hundred
# tiny cells. An industry NOT listed here falls through to its raw yfinance
# label (already human-readable). Plain "what it is" — no AI framing.
# ---------------------------------------------------------------------------
INDUSTRY_DISPLAY: dict[str, str] = {
    # --- Technology ---
    "Software - Application": "Software",
    "Software - Infrastructure": "Software",
    "Information Technology Services": "IT Services",
    "Semiconductors": "Semiconductors",
    "Semiconductor Equipment & Materials": "Semiconductor Equipment",
    "Communication Equipment": "Networking & Comms Equipment",
    "Computer Hardware": "Computer Hardware",
    "Consumer Electronics": "Consumer Electronics",
    "Electronic Components": "Electronics",
    "Electronics & Computer Distribution": "Electronics",
    "Scientific & Technical Instruments": "Instruments",
    "Solar": "Solar",
    # --- Financials ---
    "Banks - Diversified": "Banks",
    "Banks - Regional": "Banks",
    "Capital Markets": "Capital Markets",
    "Financial Data & Stock Exchanges": "Capital Markets",
    "Asset Management": "Asset Management",
    "Credit Services": "Payments & Fintech",
    "Insurance - Diversified": "Insurance",
    "Insurance - Life": "Insurance",
    "Insurance - Property & Casualty": "Insurance",
    "Insurance - Reinsurance": "Insurance",
    "Insurance - Specialty": "Insurance",
    "Insurance Brokers": "Insurance",
    "Mortgage Finance": "Mortgage Finance",
    "Financial Conglomerates": "Financial Services",
    "Shell Companies": "Financial Services",
    # --- Healthcare ---
    "Biotechnology": "Biotech",
    "Drug Manufacturers - General": "Pharmaceuticals",
    "Drug Manufacturers - Specialty & Generic": "Pharmaceuticals",
    "Medical Devices": "Medical Devices",
    "Medical Instruments & Supplies": "Medical Devices",
    "Diagnostics & Research": "Medical Devices",
    "Healthcare Plans": "Healthcare Services",
    "Medical Care Facilities": "Healthcare Services",
    "Health Information Services": "Healthcare Services",
    "Medical Distribution": "Healthcare Services",
    "Pharmaceutical Retailers": "Healthcare Services",
    # --- Industrials ---
    "Aerospace & Defense": "Aerospace & Defense",
    "Airlines": "Airlines",
    "Building Products & Equipment": "Building Products",
    "Conglomerates": "Conglomerates",
    "Electrical Equipment & Parts": "Electrical Equipment",
    "Engineering & Construction": "Engineering & Construction",
    "Farm & Heavy Construction Machinery": "Industrial Machinery",
    "Specialty Industrial Machinery": "Industrial Machinery",
    "Metal Fabrication": "Industrial Machinery",
    "Tools & Accessories": "Industrial Machinery",
    "Business Equipment & Supplies": "Industrial Machinery",
    "Pollution & Treatment Controls": "Industrial Machinery",
    "Integrated Freight & Logistics": "Transportation & Logistics",
    "Trucking": "Transportation & Logistics",
    "Railroads": "Transportation & Logistics",
    "Marine Shipping": "Transportation & Logistics",
    "Airports & Air Services": "Transportation & Logistics",
    "Rental & Leasing Services": "Rental & Leasing",
    "Consulting Services": "Business Services",
    "Staffing & Employment Services": "Business Services",
    "Specialty Business Services": "Business Services",
    "Security & Protection Services": "Business Services",
    "Industrial Distribution": "Distribution",
    "Waste Management": "Waste & Environmental",
    "Infrastructure Operations": "Engineering & Construction",
    # --- Energy ---
    "Oil & Gas Drilling": "Oil & Gas",
    "Oil & Gas E&P": "Oil & Gas",
    "Oil & Gas Equipment & Services": "Oil & Gas",
    "Oil & Gas Integrated": "Oil & Gas",
    "Oil & Gas Midstream": "Oil & Gas",
    "Oil & Gas Refining & Marketing": "Oil & Gas",
    "Thermal Coal": "Coal",
    "Coking Coal": "Coal",
    "Uranium": "Uranium",
    # --- Basic Materials ---
    "Agricultural Inputs": "Chemicals",
    "Chemicals": "Chemicals",
    "Specialty Chemicals": "Chemicals",
    "Aluminum": "Metals & Mining",
    "Copper": "Metals & Mining",
    "Gold": "Metals & Mining",
    "Silver": "Metals & Mining",
    "Steel": "Metals & Mining",
    "Other Industrial Metals & Mining": "Metals & Mining",
    "Other Precious Metals & Mining": "Metals & Mining",
    "Building Materials": "Building Materials",
    "Paper & Paper Products": "Paper & Packaging",
    "Packaging & Containers": "Paper & Packaging",
    "Lumber & Wood Production": "Paper & Packaging",
    # --- Communication Services ---
    "Internet Content & Information": "Internet & Media",
    "Advertising Agencies": "Advertising",
    "Broadcasting": "Media & Entertainment",
    "Entertainment": "Media & Entertainment",
    "Electronic Gaming & Multimedia": "Media & Entertainment",
    "Publishing": "Media & Entertainment",
    "Telecom Services": "Telecom",
    # --- Consumer Cyclical ---
    "Internet Retail": "E-commerce",
    "Auto Manufacturers": "Automakers",
    "Auto Parts": "Auto Parts",
    "Auto & Truck Dealerships": "Auto Retail",
    "Restaurants": "Restaurants",
    "Specialty Retail": "Retail",
    "Department Stores": "Retail",
    "Apparel Retail": "Retail",
    "Home Improvement Retail": "Retail",
    "Footwear & Accessories": "Apparel & Luxury",
    "Apparel Manufacturing": "Apparel & Luxury",
    "Luxury Goods": "Apparel & Luxury",
    "Travel Services": "Travel & Leisure",
    "Lodging": "Travel & Leisure",
    "Leisure": "Travel & Leisure",
    "Gambling": "Travel & Leisure",
    "Resorts & Casinos": "Travel & Leisure",
    "Residential Construction": "Homebuilding",
    "Furnishings, Fixtures & Appliances": "Home & Furnishings",
    "Packaging & Containers ": "Paper & Packaging",
    # --- Consumer Defensive ---
    "Beverages - Non-Alcoholic": "Food & Beverage",
    "Beverages - Brewers": "Food & Beverage",
    "Beverages - Wineries & Distilleries": "Food & Beverage",
    "Packaged Foods": "Food & Beverage",
    "Confectioners": "Food & Beverage",
    "Farm Products": "Food & Beverage",
    "Food Distribution": "Food & Beverage",
    "Grocery Stores": "Retail",
    "Discount Stores": "Retail",
    "Household & Personal Products": "Household Products",
    "Tobacco": "Tobacco",
    "Education & Training Services": "Education",
    # --- Utilities ---
    "Utilities - Regulated Electric": "Utilities",
    "Utilities - Regulated Gas": "Utilities",
    "Utilities - Regulated Water": "Utilities",
    "Utilities - Diversified": "Utilities",
    "Utilities - Independent Power Producers": "Power Generation",
    "Utilities - Renewable": "Power Generation",
    # --- Real Estate ---
    "REIT - Diversified": "Real Estate",
    "REIT - Industrial": "Real Estate",
    "REIT - Office": "Real Estate",
    "REIT - Retail": "Real Estate",
    "REIT - Residential": "Real Estate",
    "REIT - Healthcare Facilities": "Real Estate",
    "REIT - Hotel & Motel": "Real Estate",
    "REIT - Specialty": "Real Estate",
    "REIT - Mortgage": "Real Estate",
    "Real Estate Services": "Real Estate",
    "Real Estate - Development": "Real Estate",
    "Real Estate - Diversified": "Real Estate",
}

# Per-symbol label overrides. Two purposes:
#  1. The inference-stack functional overlay — the ~80 supply-chain names get a
#     sharper FUNCTIONAL sub-industry than yfinance's coarse bucket (SanDisk is
#     "Memory & Storage", not generic "Computer Hardware"; Dell is "Servers").
#     Labels are deliberately PLAIN functional terms — what the thing is — NOT
#     AI-marketing buzzwords ("AI Accelerators", "Neoclouds", "Hyperscalers").
#  2. A few plain fixes where yfinance is wrong (EV makers, Bitcoin miners).
# Everything NOT listed here keeps its clean yfinance industry (INDUSTRY_DISPLAY).
SYMBOL_OVERRIDE: dict[str, str] = {
    # --- Compute & custom silicon ---
    "NVDA": "GPUs & Accelerators", "AMD": "GPUs & Accelerators",
    "AVGO": "Custom Silicon", "MRVL": "Custom Silicon",
    "ALAB": "Custom Silicon", "CRDO": "Custom Silicon",
    # --- Foundry ---
    "TSM": "Foundry", "GFS": "Foundry", "UMC": "Foundry", "INTC": "Foundry",
    # --- Memory & storage ---
    "MU": "Memory & Storage", "WDC": "Memory & Storage", "STX": "Memory & Storage",
    "SNDK": "Memory & Storage", "PSTG": "Memory & Storage",
    # --- Semiconductor equipment ---
    "ASML": "Semiconductor Equipment", "AMAT": "Semiconductor Equipment",
    "LRCX": "Semiconductor Equipment", "KLAC": "Semiconductor Equipment",
    "TER": "Semiconductor Equipment", "ENTG": "Semiconductor Equipment",
    "ONTO": "Semiconductor Equipment", "KLIC": "Semiconductor Equipment",
    "ACMR": "Semiconductor Equipment", "CAMT": "Semiconductor Equipment",
    "MKSI": "Semiconductor Equipment", "AEIS": "Semiconductor Equipment",
    # --- EDA & IP ---
    "SNPS": "EDA & IP", "CDNS": "EDA & IP", "ARM": "EDA & IP",
    # --- Analog & power chips ---
    "ADI": "Analog & Power Chips", "TXN": "Analog & Power Chips",
    "MPWR": "Analog & Power Chips", "ON": "Analog & Power Chips",
    "NXPI": "Analog & Power Chips", "MCHP": "Analog & Power Chips",
    "QCOM": "Analog & Power Chips",
    # --- Networking & optical ---
    "ANET": "Networking", "CSCO": "Networking", "CIEN": "Networking", "JNPR": "Networking",
    "COHR": "Optical Components", "LITE": "Optical Components", "FN": "Optical Components",
    # --- Servers / ODM ---
    "SMCI": "Servers", "DELL": "Servers", "HPE": "Servers", "CLS": "Servers",
    # --- Cloud platforms & infrastructure ---
    "MSFT": "Cloud & Internet", "GOOGL": "Cloud & Internet", "GOOG": "Cloud & Internet",
    "AMZN": "Cloud & Internet", "META": "Cloud & Internet", "ORCL": "Cloud & Internet",
    "CRWV": "Cloud Infrastructure", "NBIS": "Cloud Infrastructure", "APLD": "Cloud Infrastructure",
    # --- Software ---
    "PLTR": "Software", "NOW": "Software", "CRM": "Software", "SNOW": "Software",
    # --- Power & grid (datacenter electricity) ---
    "CEG": "Power & Grid", "VST": "Power & Grid", "GEV": "Power & Grid",
    "ETN": "Power & Grid", "PWR": "Power & Grid", "NRG": "Power & Grid",
    "TLN": "Power & Grid", "POWL": "Power & Grid", "HUBB": "Power & Grid",
    "GNRC": "Power & Grid",
    # --- Nuclear ---
    "OKLO": "Nuclear", "SMR": "Nuclear", "LEU": "Nuclear", "BWXT": "Nuclear", "CCJ": "Nuclear",
    # --- Cooling ---
    "VRT": "Cooling", "NVT": "Cooling", "MOD": "Cooling",
    # --- Data-center REITs ---
    "EQIX": "Data Center REITs", "DLR": "Data Center REITs",
    # --- Plain fixes (yfinance wrong) ---
    "TSLA": "EV", "RIVN": "EV", "LCID": "EV",
    "MARA": "Bitcoin Mining", "RIOT": "Bitcoin Mining", "CLSK": "Bitcoin Mining",
    "WULF": "Bitcoin Mining", "IREN": "Bitcoin Mining", "CIFR": "Bitcoin Mining",
    "HUT": "Bitcoin Mining", "CORZ": "Bitcoin Mining", "BTDR": "Bitcoin Mining",
    "BTBT": "Bitcoin Mining",
}


# ---------------------------------------------------------------------------
# Screener fetch
# ---------------------------------------------------------------------------

def _clean_name(raw: str) -> str:
    name = (raw or "").strip()
    name = _NAME_SUFFIX_RE.sub("", name).strip()
    return name or raw.strip()


def _fetch_screener() -> list[dict]:
    """One call -> every US-listed name with market cap. Returns a list of
    {symbol, yf_symbol, name, mktcap} for common stocks at/above MIN_MKTCAP.
    Raises on HTTP/parse failure."""
    req = Request(SCREENER_URL, headers=SCREENER_HEADERS)
    with urlopen(req, timeout=TIMEOUT) as r:
        payload = json.loads(r.read().decode("utf-8", errors="replace"))
    rows = (payload.get("data") or {}).get("rows")
    if not rows:
        raise RuntimeError("us_universe: screener returned no rows")

    out: list[dict] = []
    for row in rows:
        symbol = str(row.get("symbol", "")).strip().upper()
        if not SYMBOL_RE.match(symbol):
            continue
        try:
            mktcap = float(row.get("marketCap") or 0)
        except (TypeError, ValueError):
            mktcap = 0.0
        if mktcap < MIN_MKTCAP:
            continue
        out.append({
            "symbol": symbol,
            "yf_symbol": symbol.replace("/", "-"),   # BRK/B -> BRK-B for yfinance
            "name": _clean_name(row.get("name", "")),
            "mktcap": mktcap,
            "nasdaq_industry": (row.get("industry") or "").strip(),
        })
    LOG.info("Screener: %d names at/above $%.0fB", len(out), MIN_MKTCAP / 1e9)
    return out


# ---------------------------------------------------------------------------
# Classification (yfinance sector/industry, cached)
# ---------------------------------------------------------------------------

def _classify(universe: list[dict], cache_path: Path) -> dict[str, dict]:
    """Return {yf_symbol: {sector, industry}} from yfinance, cached on disk.

    Classification is static, so only symbols missing from the cache trigger a
    (slow) .info call. The cache is checkpoint-persisted so a partial/interrupted
    cold-start run isn't wasted.

    A symbol is cached only when .info returns a NON-EMPTY response (even if its
    sector/industry are genuinely null — that's a real answer worth remembering).
    A throttle/timeout that raises, or an empty `{}` response, is left UNcached so
    it retries next run rather than being permanently pinned to "Other" — yfinance
    returns `{}`/429 under load, and a committed cache means a single transient
    miss on a new entrant would otherwise stick forever.
    """
    cache: dict[str, dict] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
        except Exception:
            cache = {}

    missing = [u["yf_symbol"] for u in universe if u["yf_symbol"] not in cache]
    if not missing:
        return cache

    import yfinance as yf
    LOG.info("Classifying %d new symbols via yfinance .info (cache has %d) ...",
             len(missing), len(cache))
    for i, sym in enumerate(missing):
        try:
            info = yf.Ticker(sym).info or {}
            if info:   # real response — cache it (genuine-null sector/industry included)
                cache[sym] = {"sector": info.get("sector"), "industry": info.get("industry")}
            else:      # empty `{}` = throttle/timeout; leave uncached to retry next run
                LOG.debug("classify %s: empty .info, will retry next run", sym)
        except Exception as e:
            LOG.debug("classify %s failed (will retry next run): %s", sym, e)
        if (i + 1) % INFO_CHECKPOINT == 0:
            _write_json(cache_path, cache)
            LOG.info("  classified %d/%d ...", i + 1, len(missing))
        time.sleep(INFO_SLEEP_S)
    _write_json(cache_path, cache)
    return cache


def _resolve_label(symbol: str, classification: dict | None) -> tuple[str, str | None]:
    """(display_label, gics_sector) for a stock. Override > collapsed industry >
    raw industry > sector > 'Other'."""
    cls = classification or {}
    industry = cls.get("industry")
    sector = cls.get("sector")
    if symbol in SYMBOL_OVERRIDE:
        return SYMBOL_OVERRIDE[symbol], sector
    if industry:
        return INDUSTRY_DISPLAY.get(industry, industry), sector
    if sector:
        return sector, sector
    return "Other", None


# ---------------------------------------------------------------------------
# Bulk price history (yfinance)
# ---------------------------------------------------------------------------

def _fetch_history(yf_symbols: list[str]) -> dict[str, list[dict]]:
    """Bulk-download 2y daily closes -> {yf_symbol: [{date, close}, ...]}.

    Two years so the 1y-ago anchor close is always present. Chunked into BATCH
    calls; per-batch failure is logged and skipped (those names drop out, the
    rest survive).
    """
    import pandas as pd
    import yfinance as yf

    out: dict[str, list[dict]] = {}
    batches = [yf_symbols[i:i + BATCH] for i in range(0, len(yf_symbols), BATCH)]
    for bi, batch in enumerate(batches):
        if bi:
            time.sleep(BATCH_SLEEP_S)
        try:
            df = yf.download(
                batch, period="2y", auto_adjust=True,
                progress=False, threads=True, group_by="column",
            )
        except Exception as e:
            LOG.warning("yfinance batch %d/%d failed: %s", bi + 1, len(batches), e)
            continue
        if df is None or df.empty:
            LOG.warning("yfinance batch %d/%d empty", bi + 1, len(batches))
            continue

        try:
            close = df["Close"]
        except Exception:
            close = df
        if isinstance(close, pd.Series):       # single-symbol batch
            close = close.to_frame(name=batch[0])

        for sym in batch:
            if sym not in close.columns:
                continue
            series = close[sym].dropna()
            if series.empty:
                continue
            hist = [
                {"date": idx.strftime("%Y-%m-%d"), "close": round(float(v), 4)}
                for idx, v in series.items()
                if v is not None and float(v) == float(v)  # NaN guard
            ]
            if hist:
                out[sym] = hist
        LOG.info("yfinance batch %d/%d: %d/%d symbols with history",
                 bi + 1, len(batches), sum(1 for s in batch if s in out), len(batch))
    return out


# ---------------------------------------------------------------------------
# Return computation
# ---------------------------------------------------------------------------

QUORUM_FRAC = 0.6   # a date counts as a "full session" if ≥60% of peak names traded


def _resolve_anchor_dates(all_dates: list[date], today: date) -> dict[str, date | None]:
    """Resolve the 7 window anchors against the actual trading calendar.

    `latest` = most recent FULL trading session; `d1` = the full session before
    it (previous session); w1..y1 = last trading day on-or-before the target
    calendar date.

    `latest`/`d1` use a quorum, NOT the bare global max date: `all_dates` has one
    entry per (symbol, date), so a Counter gives symbols-per-date. yfinance posts
    the new session staggered per-name right after the close — exactly when the
    22:00-UTC cron fires — so the few earliest names would pull a bare `max()`
    ahead of the pack and blank ret_1d for the majority (whose own last close
    then ≠ latest). Requiring ≥QUORUM_FRAC of the peak day's name-count keeps
    `latest` on the session the bulk of the universe has actually posted.
    """
    if not all_dates:
        return {k: None for k in ("latest", "d1", "w1", "m1", "m3", "m6", "y1")}
    freq = Counter(all_dates)
    asc = sorted(freq)                                  # every date any symbol traded
    quorum = QUORUM_FRAC * max(freq.values())
    full_days = [d for d in asc if freq[d] >= quorum]   # dates the bulk of names posted
    latest = full_days[-1] if full_days else asc[-1]
    d1 = full_days[-2] if len(full_days) >= 2 else None

    def on_or_before(target: date) -> date | None:
        prior = [d for d in asc if d <= target]
        return prior[-1] if prior else None

    return {
        "latest": latest,
        "d1":  d1,
        "w1":  on_or_before(latest - timedelta(days=7)),
        "m1":  on_or_before(latest - timedelta(days=30)),
        "m3":  on_or_before(latest - timedelta(days=91)),
        "m6":  on_or_before(latest - timedelta(days=182)),
        "y1":  on_or_before(latest - timedelta(days=365)),
    }


def _returns_for(history: list[dict], anchors: dict[str, date | None]) -> dict[str, float | None]:
    """Per-symbol pct returns vs each anchor, using the symbol's own closes."""
    by_date = {datetime.fromisoformat(h["date"]).date(): h["close"] for h in history}
    sorted_dates = sorted(by_date)
    if not sorted_dates:
        return {}
    latest_close = by_date[sorted_dates[-1]]

    def close_on_or_before(target: date | None) -> float | None:
        if target is None:
            return None
        prior = [d for d in sorted_dates if d <= target]
        if not prior:
            return None
        c = by_date[prior[-1]]
        return c if c else None

    out: dict[str, float | None] = {}
    key_to_window = {"d1": "1d", "w1": "1w", "m1": "1m", "m3": "3m", "m6": "6m", "y1": "1y"}
    for akey, wlabel in key_to_window.items():
        ref = close_on_or_before(anchors.get(akey))
        if ref and ref > 0 and latest_close:
            out[f"ret_{wlabel}"] = round((latest_close / ref - 1) * 100, 1)
        else:
            out[f"ret_{wlabel}"] = None

    # 1D is the just-closed session's move. If this symbol has no close on the
    # universe's latest trading day (its yfinance data lags a session — common
    # right after the close, before the vendor posts every name), the d1 anchor
    # coincides with the symbol's own stale last close and fabricates a 0.0%
    # move. Report None so a stale name shows "—" rather than a fake flat day
    # (which would also drag its industry's median_1d toward zero). Longer
    # windows absorb a one-day lag harmlessly, so only 1D needs this guard.
    if sorted_dates[-1] != anchors.get("latest"):
        out["ret_1d"] = None
    return out


def _compute_sector_medians(stocks: list[dict]) -> list[dict]:
    """Group by display industry label, median return per window. (Frontend
    recomputes client-side over the active floor — this is a convenience copy.)"""
    windows = ["1d", "1w", "1m", "3m", "6m", "1y"]
    by: dict[str, list[dict]] = {}
    for s in stocks:
        by.setdefault(s.get("industry_en") or "Other", []).append(s)

    sectors = []
    for label, members in by.items():
        sector: dict[str, Any] = {"industry": label, "industry_en": label, "n": len(members)}
        for w in windows:
            vals = [m[f"ret_{w}"] for m in members if m.get(f"ret_{w}") is not None]
            sector[f"median_{w}"] = round(median(vals), 1) if vals else None
        sectors.append(sector)
    # (is None, -v): nulls last; `or 0.0` is safe here — the only falsy median is
    # 0.0 itself (→ 0.0) and None (already sorted last by the first key).
    sectors.sort(key=lambda x: (x.get("median_3m") is None, -(x.get("median_3m") or 0.0)))
    return sectors


# ---------------------------------------------------------------------------
# Tracked symbols (dashboard players)
# ---------------------------------------------------------------------------

def _load_tracked_symbols(players_path: Path) -> set[str]:
    """Bare US symbols among dashboard players (tickers with no foreign suffix)."""
    if not players_path.exists():
        return set()
    try:
        players = json.loads(players_path.read_text())
    except Exception:
        return set()
    return {str(p.get("ticker", "")).upper() for p in players
            if p.get("ticker") and "." not in str(p["ticker"])}


# ---------------------------------------------------------------------------
# Atomic write (standalone helper; refresh.py uses its own _write_json)
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch(existing: dict | None = None) -> dict:
    """Fetch the US large-cap universe, compute multi-window returns, emit payload.

    Raises on unrecoverable failure so the caller preserves the prior file.
    """
    today = date.today()
    root = Path(__file__).resolve().parent.parent.parent

    universe = _fetch_screener()
    if not universe:
        raise RuntimeError("us_universe: empty universe after screener filter")

    # Classification (cached): plain industry per symbol.
    classification = _classify(universe, root / "data" / "us_industry.json")

    yf_symbols = [u["yf_symbol"] for u in universe]
    LOG.info("Fetching 2y history for %d symbols (batches of %d) ...", len(yf_symbols), BATCH)
    hist_by_symbol = _fetch_history(yf_symbols)
    if not hist_by_symbol:
        raise RuntimeError("us_universe: yfinance returned no history for any symbol")

    # Global trading calendar -> window anchor dates.
    all_dates: list[date] = []
    for hist in hist_by_symbol.values():
        all_dates.extend(datetime.fromisoformat(h["date"]).date() for h in hist)
    anchors = _resolve_anchor_dates(all_dates, today)

    tracked = _load_tracked_symbols(root / "data" / "players.json")

    stocks: list[dict] = []
    for u in universe:
        hist = hist_by_symbol.get(u["yf_symbol"])
        if not hist:
            continue
        rets = _returns_for(hist, anchors)
        label, sector = _resolve_label(u["symbol"], classification.get(u["yf_symbol"]))
        stocks.append({
            "symbol": u["symbol"],
            "name": u["name"],
            "sector": sector,                 # GICS sector (yfinance), for reference
            "industry": label,
            "industry_en": label,
            "nasdaq_industry": u["nasdaq_industry"],
            "close": hist[-1]["close"],
            "mktcap": round(u["mktcap"]),
            "pe": None,                       # screener has no P/E; column omitted on the page
            "ret_1d": rets.get("ret_1d"),
            "ret_1w": rets.get("ret_1w"),
            "ret_1m": rets.get("ret_1m"),
            "ret_3m": rets.get("ret_3m"),
            "ret_6m": rets.get("ret_6m"),
            "ret_1y": rets.get("ret_1y"),
            "tracked": u["symbol"] in tracked,
        })

    # Degraded-write guard: per-batch yfinance failures only drop names (they
    # don't raise), so a partially-throttled run — likely from a cloud IP — would
    # otherwise silently ship a truncated universe with skewed medians and a green
    # "ok". If the assembled count collapses to <50% of the prior file, raise so
    # the caller's except-branch preserves the prior us_movers.json instead.
    prior_count = (existing or {}).get("count") or len((existing or {}).get("stocks") or [])
    if prior_count and len(stocks) < 0.5 * prior_count:
        raise RuntimeError(
            f"us_universe: only {len(stocks)} names assembled vs prior {prior_count} "
            f"(<50%) — likely a partial yfinance fetch; preserving prior file"
        )

    # Sort by ret_3m descending (primary wave-1 window), nulls last.
    stocks.sort(key=lambda s: (s.get("ret_3m") is None, -(s.get("ret_3m") or 0)))
    sectors = _compute_sector_medians(stocks)

    dates_iso = {k: (d.isoformat() if d else None) for k, d in anchors.items()}
    LOG.info("us_universe: %d stocks assembled, %d industries, latest=%s",
             len(stocks), len(sectors), dates_iso.get("latest"))

    return {
        "as_of": today.isoformat(),
        "dates": dates_iso,
        "count": len(stocks),
        "min_mktcap": MIN_MKTCAP,
        "stocks": stocks,
        "sectors": sectors,
    }


# ---------------------------------------------------------------------------
# Standalone entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    root = Path(__file__).resolve().parent.parent.parent
    out_path = root / "data" / "us_movers.json"
    prev = {}
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text())
        except Exception:
            pass

    try:
        result = fetch(existing=prev)
        _write_json(out_path, result)
        print(f"OK: {result['count']} stocks written to {out_path}")
        print(f"Dates: {result['dates']}")
        print(f"\nTop 14 industries by 3M median:")
        for s in result["sectors"][:14]:
            m3 = s.get("median_3m")
            print(f"  {s['industry_en']:28s}  n={s['n']:4d}  "
                  f"3m={m3:+.1f}%" if m3 is not None else f"  {s['industry_en']:28s}  n={s['n']:4d}  3m=None")
        print(f"\nTop 12 movers by 3M:")
        for s in result["stocks"][:12]:
            m3 = s.get("ret_3m")
            print(f"  {s['symbol']:6s} {s['name'][:24]:24s} {s['industry_en']:24s} "
                  f"3m={m3:+.1f}%" if m3 is not None else f"  {s['symbol']:6s} 3m=None")
    except Exception as e:
        LOG.error("us_universe failed: %s", e)
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
