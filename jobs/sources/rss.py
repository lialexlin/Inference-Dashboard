"""RSS-based signal collection across the inference-stack tracking sources.

Each entry returned is a raw signal-shaped dict; transform.py tags it to layers
and merges with curated SIGNALS.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)


# (name, url, source_type) — keep this list editable; broken feeds are tolerated.
FEEDS: list[tuple[str, str, str]] = [
    ("TrendForce", "https://www.trendforce.com/news/feed/", "industry"),
    ("Reuters Tech", "https://news.google.com/rss/search?q=site:reuters.com+(semiconductor+OR+HBM+OR+AI+chip)&hl=en-US&gl=US&ceid=US:en", "news"),
    ("DigiTimes", "https://news.google.com/rss/search?q=site:digitimes.com+(semiconductor+OR+TSMC+OR+CoWoS)&hl=en-US&gl=US&ceid=US:en", "industry"),
    ("Tom's Hardware", "https://www.tomshardware.com/feeds/all", "news"),
    ("ServeTheHome", "https://www.servethehome.com/feed/", "news"),
    ("The Register", "https://www.theregister.com/data_centre/headlines.atom", "news"),
    ("SemiAnalysis", "https://semianalysis.com/feed/", "analyst"),
    ("Mule Capital", "https://mulecap.substack.com/feed", "analyst"),
    ("Stratechery", "https://stratechery.com/feed/", "analyst"),
    ("AnandTech (Wayback)", "https://www.anandtech.com/rss/", "news"),
]


@dataclass
class RSSResult:
    entries: list[dict] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)
    per_source_counts: dict[str, int] = field(default_factory=dict)


def _stable_id(source: str, url: str, title: str) -> str:
    h = hashlib.sha1(f"{source}|{url}|{title}".encode("utf-8")).hexdigest()[:16]
    return f"rss-{h}"


def _parse_date(entry) -> str:
    for key in ("published_parsed", "updated_parsed"):
        v = entry.get(key)
        if v:
            try:
                return datetime(*v[:6], tzinfo=timezone.utc).date().isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).date().isoformat()


def _summary(entry) -> str:
    raw = entry.get("summary") or entry.get("description") or ""
    if not raw:
        return ""
    import html as _html
    import re
    text = re.sub(r"<[^>]+>", " ", raw)
    text = _html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


def fetch(max_per_source: int = 25) -> RSSResult:
    import feedparser

    result = RSSResult()
    for name, url, source_type in FEEDS:
        try:
            parsed = feedparser.parse(url, agent="Mozilla/5.0 InferenceDashboard/0.1")
            if parsed.bozo and not parsed.entries:
                raise RuntimeError(f"bozo: {parsed.bozo_exception}")
            count = 0
            for entry in parsed.entries[:max_per_source]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue
                signal = {
                    "id": _stable_id(name, link, title),
                    "date": _parse_date(entry),
                    "source": name,
                    "source_type": source_type,
                    "headline": title,
                    "quote": _summary(entry),
                    "url": link,
                    "layer_ids": [],   # filled in by transform.py
                    "tickers": [],     # filled in by transform.py
                }
                result.entries.append(signal)
                count += 1
            result.per_source_counts[name] = count
            log.info("OK %s: %d entries", name, count)
        except Exception as e:
            log.warning("FAIL %s: %s", name, e)
            result.errors[name] = str(e)
            result.per_source_counts[name] = 0
    return result
