"""Everything that pulls data from the outside world: RSS feeds, FRED numbers,
and full article text."""

import csv
import html
import io
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import feedparser
import trafilatura

from sources import INDICATORS

MAX_CANDIDATES = 45          # headlines sent to the editor per section
MAX_AGE = timedelta(hours=48)
FULLTEXT_CHARS = 8000        # per source, keeps prompts (and cost) bounded
USER_AGENT = "Mozilla/5.0 (compatible; DailySpinBot/0.2)"


def fetch_bytes(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def clean_text(raw: str, limit: int = 400) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text[:limit]


# ---------------------------------------------------------------- RSS

def fetch_feed(source: str, url: str) -> list[dict]:
    try:
        parsed = feedparser.parse(fetch_bytes(url))
    except Exception as e:  # network errors, timeouts, 403s...
        print(f"  ! {source}: {e}", file=sys.stderr)
        return []
    now = datetime.now(timezone.utc)
    items = []
    for entry in parsed.entries[:30]:
        stamp = entry.get("published_parsed") or entry.get("updated_parsed")
        published = datetime(*stamp[:6], tzinfo=timezone.utc) if stamp else None
        if published and now - published > MAX_AGE:
            continue
        title = clean_text(entry.get("title", ""), 200)
        if not title or not entry.get("link"):
            continue
        items.append({
            "source": source,
            "title": title,
            "summary": clean_text(entry.get("summary", "")),
            "url": entry.get("link"),
            "published": published.isoformat() if published else None,
        })
    print(f"  {source}: {len(items)} items")
    return items


def gather_section(feeds: dict) -> list[dict]:
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = pool.map(lambda kv: fetch_feed(*kv), feeds.items())
    # Interleave feeds so no single outlet dominates the candidate list.
    per_feed = [r for r in results if r]
    items, seen = [], set()
    for i in range(max((len(r) for r in per_feed), default=0)):
        for feed_items in per_feed:
            if i < len(feed_items):
                item = feed_items[i]
                key = re.sub(r"[^a-z0-9]", "", item["title"].lower())[:60]
                if key not in seen:
                    seen.add(key)
                    items.append(item)
    items = items[:MAX_CANDIDATES]
    for idx, item in enumerate(items):
        item["id"] = idx
    return items


# ---------------------------------------------------------------- full text

def fetch_fulltext(item: dict) -> str:
    """Main article text, or the RSS summary when the site blocks us."""
    try:
        text = trafilatura.extract(fetch_bytes(item["url"], 15), include_comments=False) or ""
    except Exception:
        text = ""
    if len(text) < 300:
        return item["summary"]
    return text[:FULLTEXT_CHARS]


def fetch_fulltexts(items: list[dict]) -> None:
    """Adds item["text"] in place, in parallel."""
    with ThreadPoolExecutor(max_workers=8) as pool:
        for item, text in zip(items, pool.map(fetch_fulltext, items)):
            item["text"] = text


# ---------------------------------------------------------------- FRED

def fetch_indicators() -> list[dict]:
    out = []
    for ind in INDICATORS:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ind['id']}"
        try:
            rows = list(csv.reader(io.StringIO(fetch_bytes(url).decode())))[1:]
            rows = [(d, float(v)) for d, v in rows if v not in ("", ".")]
            date, value = rows[-1]
            prev = rows[-2][1]
            if ind.get("yoy"):
                # Match by calendar date, not row count: FRED series can have gaps
                # (e.g. no October 2025 CPI because of the government shutdown).
                by_date = dict(rows)
                def yoy(d: str) -> float | None:
                    base = by_date.get(f"{int(d[:4]) - 1}{d[4:]}")
                    return (by_date[d] / base - 1) * 100 if base else None
                value, prev = yoy(date), yoy(rows[-2][0])
                if value is None:
                    raise ValueError("no value 12 months earlier")
                prev = value if prev is None else prev
            out.append({"label": ind["label"], "value": round(value, 2),
                        "change": round(value - prev, 2), "unit": ind["unit"], "as_of": date})
        except Exception as e:
            print(f"  ! FRED {ind['id']}: {e}", file=sys.stderr)
    return out
