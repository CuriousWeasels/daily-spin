"""Everything that pulls data from the outside world: RSS feeds, FRED numbers,
and full article text."""

import csv
import json
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


# ---------------------------------------------------------------- SPY (live quote feeds)

QUOTE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def _quote_json(url: str, extra: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": QUOTE_UA, "Accept": "application/json", **(extra or {})})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def _money(s: str) -> float:
    return float(re.sub(r"[^\d.\-]", "", s))


def fetch_spy(ind: dict) -> dict:
    """SPY's regular-session close plus, when one is running or just ended, the pre-market or
    after-hours price. Sources: Nasdaq.com's quote feed for the figures (it labels the session),
    Yahoo Finance's chart feed for three months of daily closes. Both are unofficial public
    endpoints, so either may change or refuse; overnight (8 PM - 4 AM ET) trading isn't available."""
    chart = _quote_json("https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&range=3mo")["chart"]["result"][0]
    days = [(datetime.fromtimestamp(t, timezone.utc).date().isoformat(), c)
            for t, c in zip(chart["timestamp"], chart["indicators"]["quote"][0]["close"]) if c is not None]
    value, prev, as_of = days[-1][1], days[-2][1], days[-1][0]
    session = None
    try:
        q = _quote_json("https://api.nasdaq.com/api/quote/SPY/info?assetclass=etf",
                        {"Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"})["data"]
        primary, secondary = q["primaryData"], q.get("secondaryData") or {}
        if secondary.get("lastSalePrice"):
            # An extended session is running (or just ended): secondary is the regular close,
            # primary is the latest extended-hours trade, changed against that close.
            value, change_pct = _money(secondary["lastSalePrice"]), _money(secondary["percentageChange"])
            prev = value / (1 + change_pct / 100)
            stamp = re.search(r"(\w{3} \d{1,2}, \d{4}) (\d{1,2}):(\d{2}) (AM|PM) ET", primary["lastTradeTimestamp"])
            if stamp:
                hour = int(stamp.group(2)) % 12 + (12 if stamp.group(4) == "PM" else 0)
                minutes = hour * 60 + int(stamp.group(3))
                name = "After hours" if minutes >= 16 * 60 else "Pre-market" if minutes < 9 * 60 + 30 else "Extended"
                session = {"label": name, "price": _money(primary["lastSalePrice"]),
                           "change_pct": _money(primary["percentageChange"]),
                           "time": f"{stamp.group(2)}:{stamp.group(3)} {stamp.group(4)} ET",
                           "date": datetime.strptime(stamp.group(1), "%b %d, %Y").date().isoformat()}
                close_stamp = re.search(r"(\w{3} \d{1,2}, \d{4})", secondary.get("lastTradeTimestamp", ""))
                if close_stamp:
                    as_of = datetime.strptime(close_stamp.group(1), "%b %d, %Y").date().isoformat()
        else:
            value = _money(primary["lastSalePrice"])
            prev = value / (1 + _money(primary["percentageChange"]) / 100)
    except Exception as e:
        print(f"  ! SPY session quote unavailable ({e}); using Yahoo close only", file=sys.stderr)
    history = [round(c, 3) for _, c in days[-66:]]
    if as_of > days[-1][0]:
        history.append(round(value, 3))
    return {"id": "SPY", "label": ind["label"], "kind": ind["kind"], "unit": ind["unit"],
            "unit_label": ind.get("unit_label"), "value": round(value, 2), "change": round(value - prev, 2),
            "change_pct": round((value / prev - 1) * 100, 2), "as_of": as_of,
            "history": history, "since": days[-66:][0][0], "session": session}


# ---------------------------------------------------------------- FRED

def fetch_indicators() -> list[dict]:
    out = []
    for ind in INDICATORS:
        if ind.get("source") == "quote":
            try:
                out.append(fetch_spy(ind))
            except Exception as e:
                print(f"  ! SPY quote: {e}", file=sys.stderr)
            continue
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ind['id']}"
        try:
            rows = list(csv.reader(io.StringIO(fetch_bytes(url).decode())))[1:]
            rows = [(d, float(v)) for d, v in rows if v not in ("", ".")]
            if ind.get("yoy"):
                # Match by calendar date, not row count: FRED series can have gaps
                # (e.g. no October 2025 CPI because of the government shutdown).
                by_date = dict(rows)
                def yoy(d: str) -> float | None:
                    base = by_date.get(f"{int(d[:4]) - 1}{d[4:]}")
                    return (by_date[d] / base - 1) * 100 if base else None
                rows = [(d, yoy(d)) for d, _ in rows]
                rows = [(d, v) for d, v in rows if v is not None]
            date, value = rows[-1]
            prev = rows[-2][1]
            # Recent history for the sparkline: ~3 months of daily data, 2 years of monthly.
            span = 24 if ind.get("monthly") else 66
            out.append({"id": ind["id"], "label": ind["label"], "kind": ind.get("kind", "rate"),
                        "value": round(value, 2), "change": round(value - prev, 2),
                        "change_pct": round((value / prev - 1) * 100, 2) if prev else 0.0,
                        "unit": ind["unit"], "unit_label": ind.get("unit_label"), "as_of": date,
                        "history": [round(v, 3) for _, v in rows[-span:]],
                        "since": rows[-span:][0][0]})
        except Exception as e:
            print(f"  ! FRED {ind['id']}: {e}", file=sys.stderr)
    return out
