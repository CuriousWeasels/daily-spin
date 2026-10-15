"""Fetch free news feeds, have Claude Haiku rewrite the top stories with a
satirical tone, and write a static site to docs/.

    python build.py            # full run (needs ANTHROPIC_API_KEY)
    python build.py --no-ai    # skip Claude; shows raw headlines (free, for testing layout)
"""

import argparse
import csv
import html
import io
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
from pydantic import BaseModel

from render import render_site
from sources import INDICATORS, SECTIONS

MODEL = "claude-haiku-5-5"
STORIES_PER_SECTION = 6
MAX_CANDIDATES = 45          # headlines sent to Claude per section
MAX_AGE = timedelta(hours=48)
USER_AGENT = "Mozilla/5.0 (compatible; SatireNewsBot/0.1)"

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "docs"

SYSTEM_PROMPT = """You are the head writer of "The Daily Spin", a satirical news digest.
Think The Onion's deadpan meets a sharp Bloomberg columnist: readers should laugh AND come away accurately informed.

You receive a numbered list of real headlines with short summaries from several outlets. Your job:
1. Pick the most important stories for the section (prefer stories several outlets cover, real consequences, big numbers). Skip duplicates, listicles, deals/coupons, podcasts, and opinion pieces.
2. Rewrite each one entirely in your own words. Never copy sentences or distinctive phrases from the summaries.

Rules for the writing:
- The facts must stay true. Who, what, where, and every number must match the source. Never invent quotes, numbers, people, or events. If a detail isn't in the source, leave it out.
- The humor lives in framing, word choice, and dry asides, not in fake facts.
- Punch up at the powerful (governments, central banks, CEOs, markets, hype cycles). Never mock victims, casualties, or vulnerable people. For stories involving deaths, war casualties, or disasters, keep the tone dry and restrained, or skip the joke and simply be clear.
- Headline: punchy, under 14 words, funny but still tells you what happened.
- Summary: 2-4 sentences. First sentence states plainly what actually happened. Then the wit.
- Plain language a smart non-expert understands. Explain jargon (e.g. what a yield move means) in a quick aside."""


class Story(BaseModel):
    source_ids: list[int]   # ids of the input items this story is based on
    headline: str
    summary: str


class SectionDraft(BaseModel):
    stories: list[Story]


# ---------------------------------------------------------------- fetching

def fetch_bytes(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def clean_text(raw: str, limit: int = 400) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text[:limit]


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
    for idx, item in enumerate(items[:MAX_CANDIDATES]):
        item["id"] = idx
    return items[:MAX_CANDIDATES]


def fetch_indicators() -> list[dict]:
    out = []
    for ind in INDICATORS:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ind['id']}"
        try:
            rows = list(csv.reader(io.StringIO(fetch_bytes(url).decode())))[1:]
            rows = [(d, float(v)) for d, v in rows if v not in ("", ".")]
            date, value = rows[-1]
            if ind.get("yoy"):
                value = (value / rows[-13][1] - 1) * 100
            prev = rows[-2][1] if not ind.get("yoy") else (rows[-2][1] / rows[-14][1] - 1) * 100
            out.append({"label": ind["label"], "value": round(value, 2),
                        "change": round(value - prev, 2), "unit": ind["unit"], "as_of": date})
        except Exception as e:
            print(f"  ! FRED {ind['id']}: {e}", file=sys.stderr)
    return out


# ---------------------------------------------------------------- rewriting

def rewrite_section(client, title: str, items: list[dict], indicators: list[dict]) -> tuple[list[dict], tuple[int, int]]:
    listing = "\n".join(
        f"[{it['id']}] ({it['source']}) {it['title']} -- {it['summary']}" for it in items
    )
    extra = ""
    if title.startswith("Markets") and indicators:
        nums = "; ".join(f"{i['label']}: {i['value']}{i['unit']} (as of {i['as_of']})" for i in indicators)
        extra = f"\n\nLatest official data you may reference (these numbers are accurate): {nums}"
    prompt = (
        f"Section: {title}\n"
        f"Pick the top {STORIES_PER_SECTION} stories and rewrite them. "
        f"In source_ids, list every input id the story draws on.{extra}\n\n{listing}"
    )
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
        output_format=SectionDraft,
    )
    u = response.usage
    usage = (u.input_tokens, u.output_tokens)
    print(f"  {title}: {u.input_tokens} in / {u.output_tokens} out tokens")
    if response.stop_reason == "refusal" or response.parsed_output is None:
        print(f"  ! {title}: model declined ({response.stop_reason}); using raw headlines", file=sys.stderr)
        return raw_stories(items), usage

    by_id = {it["id"]: it for it in items}
    stories = []
    for s in response.parsed_output.stories[:STORIES_PER_SECTION]:
        refs = [by_id[i] for i in s.source_ids if i in by_id]
        if not refs:  # never publish a story we can't link back to a real source
            continue
        stories.append({
            "headline": s.headline,
            "summary": s.summary,
            "sources": [{"name": r["source"], "url": r["url"]} for r in refs],
            "published": refs[0]["published"],
        })
    return stories, usage


def raw_stories(items: list[dict]) -> list[dict]:
    return [{
        "headline": it["title"],
        "summary": it["summary"],
        "sources": [{"name": it["source"], "url": it["url"]}],
        "published": it["published"],
    } for it in items[:STORIES_PER_SECTION]]


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ai", action="store_true", help="skip Claude, show raw headlines")
    args = parser.parse_args()

    client = None
    if not args.no_ai:
        import anthropic
        client = anthropic.Anthropic()

    print("Fetching indicators...")
    indicators = fetch_indicators()

    sections, tokens_in, tokens_out = [], 0, 0
    for key, cfg in SECTIONS.items():
        print(f"Fetching {cfg['title']}...")
        items = gather_section(cfg["feeds"])
        if not items:
            stories = []
        elif client:
            stories, (i, o) = rewrite_section(client, cfg["title"], items, indicators)
            tokens_in, tokens_out = tokens_in + i, tokens_out + o
        else:
            stories = raw_stories(items)
        sections.append({"key": key, "title": cfg["title"], "stories": stories})

    now = datetime.now(timezone.utc)
    # Haiku 5.5 list price: $0.10 / 1M input, $0.50 / 1M output
    cost = tokens_in / 1e6 * 0.10 + tokens_out / 1e6 * 0.50
    data = {
        "generated_at": now.isoformat(),
        "model": MODEL if client else None,
        "cost_usd": round(cost, 5),
        "indicators": indicators,
        "sections": sections,
    }

    OUT_DIR.mkdir(exist_ok=True)
    archive = OUT_DIR / "data" / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    (OUT_DIR / "data" / "latest.json").write_text(payload, encoding="utf-8")
    (archive / f"{now:%Y-%m-%d_%H%M}.json").write_text(payload, encoding="utf-8")
    (OUT_DIR / "index.html").write_text(render_site(data), encoding="utf-8")
    print(f"Done. Wrote {OUT_DIR / 'index.html'}  (est. API cost this run: ${cost:.4f})")


if __name__ == "__main__":
    main()
