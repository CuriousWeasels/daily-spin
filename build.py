"""Build The Daily Spin: fetch free news, have Claude Sonnet write satirical
full-length articles, and write a static newspaper site to docs/.

Pipeline per run:
  1. Editor   (one call per section)  picks the top stories, grouping outlets that cover the same event
  2. Fetch    full article text from each story's sources
  3. Writer   (Message Batches API, 50% cheaper)  writes one article per story
  4. Briefing (one call)  picks the lead, writes "5 Things" and the "Number of the Day"

    python build.py                    # full run (needs ANTHROPIC_API_KEY)
    python build.py --per-section 2    # smaller, cheaper test run
    python build.py --no-ai            # no Claude at all: placeholder articles, for layout only
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from anthropic.lib._parse._transform import transform_schema
from pydantic import BaseModel, ValidationError

import fetch
import images
from prompts import BRIEFING_PROMPT, CARTOONIST_PROMPT, EDITOR_PROMPT, PHOTO_PICKER_PROMPT, WRITER_PROMPT
from render import write_site
from sources import SECTIONS

MODEL = "claude-sonnet-5-5"
EFFORT = "medium"
STORIES_PER_SECTION = 5
SOURCES_PER_STORY = 3
BATCH_TIMEOUT = 3 * 60 * 60        # seconds; most batches finish in minutes
PRICE_IN, PRICE_OUT = 2.00, 10.00  # Sonnet 5.5, $ per 1M tokens (batch is half)

# Real-time calls opt into server-side fallback: if Sonnet 5.5 declines a request
# in a category Anthropic reroutes, the API retries it on another model in the same call.
FALLBACK = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}

OUT_DIR = Path(__file__).parent / "docs"


class Pick(BaseModel):
    source_ids: list[int]
    working_title: str


class EditorPicks(BaseModel):
    stories: list[Pick]


class Article(BaseModel):
    headline: str
    dek: str
    catch_up: str
    why_it_matters: str
    body: list[str]
    topics: list[str]
    image_query: str


class PhotoChoice(BaseModel):
    story: int
    candidate: int          # -1 when no candidate fits


class PhotoChoices(BaseModel):
    choices: list[PhotoChoice]


class Cartoon(BaseModel):
    concept: str
    caption: str
    alt: str
    svg: str
    skip: bool


class NumberOfTheDay(BaseModel):
    figure: str
    explanation: str


class Briefing(BaseModel):
    lead_index: int
    five_things: list[str]
    number_of_the_day: NumberOfTheDay


class Costs:
    def __init__(self):
        self.usd = 0.0

    def add(self, usage, batch: bool = False) -> None:
        factor = 0.5 if batch else 1.0
        tokens_in = (usage.input_tokens + (usage.cache_creation_input_tokens or 0) * 1.25
                     + (usage.cache_read_input_tokens or 0) * 0.1)
        self.usd += factor * (tokens_in * PRICE_IN + usage.output_tokens * PRICE_OUT) / 1e6


def listing(items: list[dict]) -> str:
    return "\n".join(f"[{it['id']}] ({it['source']}) {it['title']} -- {it['summary']}" for it in items)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


# ---------------------------------------------------------------- 1. editor

def pick_stories(client, costs: Costs, title: str, items: list[dict], n: int, already: list[str]) -> list[Pick]:
    prompt = f"Section: {title}\nPick the top {n} stories."
    if already:
        covered = "\n".join(f"- {t}" for t in already)
        prompt += f"\n\nAlready covered in other sections. Do not pick these events again:\n{covered}"
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=EDITOR_PROMPT,
        output_config={"effort": EFFORT},
        messages=[{"role": "user", "content": f"{prompt}\n\n{listing(items)}"}],
        output_format=EditorPicks,
        **FALLBACK,
    )
    costs.add(response.usage)
    if response.stop_reason == "refusal" or response.parsed_output is None:
        print(f"  ! editor declined {title} ({response.stop_reason})", file=sys.stderr)
        return []
    valid = {it["id"] for it in items}
    picks = []
    for p in response.parsed_output.stories:
        p.source_ids = [i for i in p.source_ids if i in valid][:SOURCES_PER_STORY]
        if p.source_ids:
            picks.append(p)
    return picks[:n]


# ---------------------------------------------------------------- 3. writer (batch)

def writer_request(story: dict, indicators: list[dict]) -> dict:
    parts = [f"Section: {story['section_title']}\n"]
    for i, src in enumerate(story["source_items"], 1):
        parts.append(f"=== SOURCE {i}: {src['source']} ===\nHeadline: {src['title']}\n{src['text']}\n")
    if story["section"] == "markets" and indicators:
        nums = "; ".join(f"{i['label']}: {i['value']}{i['unit']} (as of {i['as_of']})" for i in indicators)
        parts.append(f"Latest official data (accurate, usable as a source): {nums}\n")
    parts.append("Write the article.")
    return {
        "custom_id": story["id"][:64],
        "params": {
            "model": MODEL,
            "max_tokens": 16000,
            "system": [{"type": "text", "text": WRITER_PROMPT, "cache_control": {"type": "ephemeral"}}],
            "output_config": {"effort": EFFORT,
                              "format": {"type": "json_schema", "schema": transform_schema(Article)}},
            "messages": [{"role": "user", "content": "\n".join(parts)}],
        },
    }


def write_articles(client, costs: Costs, stories: list[dict], indicators: list[dict]) -> dict[str, Article]:
    batch = client.messages.batches.create(requests=[writer_request(s, indicators) for s in stories])
    print(f"  batch {batch.id}: {len(stories)} articles queued")
    started, canceled = time.monotonic(), False
    while batch.processing_status != "ended":
        if not canceled and time.monotonic() - started > BATCH_TIMEOUT:
            print("  ! batch timed out; keeping whatever finished", file=sys.stderr)
            client.messages.batches.cancel(batch.id)
            canceled = True
        time.sleep(30)
        batch = client.messages.batches.retrieve(batch.id)
        c = batch.request_counts
        print(f"  ... {c.succeeded} done, {c.processing} writing, {c.errored} errored")

    articles = {}
    for result in client.messages.batches.results(batch.id):
        if result.result.type != "succeeded":
            print(f"  ! {result.custom_id}: {result.result.type}", file=sys.stderr)
            continue
        msg = result.result.message
        costs.add(msg.usage, batch=True)
        if msg.stop_reason != "end_turn":
            print(f"  ! {result.custom_id}: stopped ({msg.stop_reason})", file=sys.stderr)
            continue
        text = next((b.text for b in msg.content if b.type == "text"), "")
        try:
            articles[result.custom_id] = Article.model_validate_json(text)
        except ValidationError as e:
            print(f"  ! {result.custom_id}: bad JSON ({e.error_count()} errors)", file=sys.stderr)
    return articles


# ---------------------------------------------------------------- 4. briefing

def write_briefing(client, costs: Costs, articles: list[dict]) -> Briefing | None:
    lines = [
        f"[{i}] ({a['section_title']}) {a['headline']} -- {a['dek']} {' '.join(a['body'][:2])}"
        for i, a in enumerate(articles)
    ]
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=BRIEFING_PROMPT,
        output_config={"effort": EFFORT},
        messages=[{"role": "user", "content": "\n\n".join(lines)}],
        output_format=Briefing,
        **FALLBACK,
    )
    costs.add(response.usage)
    if response.stop_reason == "refusal" or response.parsed_output is None:
        return None
    b = response.parsed_output
    if not 0 <= b.lead_index < len(articles):
        b.lead_index = 0
    return b


# ---------------------------------------------------------------- 5. photos

def add_photos(client, costs: Costs, articles: list[dict]) -> None:
    """Find an openly licensed illustrative photo per article; Claude picks among the candidates."""
    found = images.search_all([a.get("image_query", "") for a in articles])
    blocks = []
    for i, (a, cands) in enumerate(zip(articles, found)):
        if cands:
            options = "\n".join(f"  ({j}) {c['title']} -- tags: {', '.join(c['tags'])}" for j, c in enumerate(cands))
            blocks.append(f"[{i}] {a['headline']} (search: {a.get('image_query', '')})\n{options}")
    if not blocks:
        return
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=PHOTO_PICKER_PROMPT,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": "\n\n".join(blocks)}],
        output_format=PhotoChoices,
        **FALLBACK,
    )
    costs.add(response.usage)
    if response.stop_reason == "refusal" or response.parsed_output is None:
        print(f"  ! photo picker declined ({response.stop_reason})", file=sys.stderr)
        return
    for ch in response.parsed_output.choices:
        if 0 <= ch.story < len(articles) and 0 <= ch.candidate < len(found[ch.story]):
            articles[ch.story]["image"] = images.to_image(found[ch.story][ch.candidate])
    print(f"  {sum(1 for a in articles if a.get('image'))} of {len(articles)} articles have a photo")


# ---------------------------------------------------------------- 6. cartoon

def draw_cartoon(client, costs: Costs, a: dict) -> dict | None:
    """A Claude-drawn single-panel cartoon for the lead story, saved as a sanitized SVG file."""
    story = (f"Section: {a['section_title']}\nHeadline: {a['headline']}\nSubheadline: {a['dek']}\n"
             f"Why it matters: {a['why_it_matters']}\n\n" + "\n\n".join(a["body"]))
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=48000,
        system=CARTOONIST_PROMPT,
        output_config={"effort": "high"},
        messages=[{"role": "user", "content": story}],
        output_format=Cartoon,
        **FALLBACK,
    ) as stream:
        msg = stream.get_final_message()
    costs.add(msg.usage)
    if msg.stop_reason != "end_turn":
        print(f"  ! cartoon not drawn ({msg.stop_reason})", file=sys.stderr)
        return None
    try:
        cartoon = msg.parsed_output or Cartoon.model_validate_json(
            next(b.text for b in msg.content if b.type == "text"))
    except (ValidationError, StopIteration):
        print("  ! cartoon came back malformed", file=sys.stderr)
        return None
    if cartoon.skip:
        print(f"  cartoonist skipped this story: {cartoon.concept}")
        return None
    svg = images.sanitize_svg(cartoon.svg)
    if svg is None:
        print("  ! cartoon SVG failed validation", file=sys.stderr)
        return None
    path = OUT_DIR / "comics" / f"{a['id']}.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    print(f"  cartoon: {cartoon.concept}")
    return {"file": f"comics/{a['id']}.svg", "caption": cartoon.caption, "alt": cartoon.alt}


# ---------------------------------------------------------------- no-AI placeholders

def placeholder(story: dict) -> Article:
    src = story["source_items"][0]
    return Article(headline=src["title"], dek=src["summary"][:160],
                   catch_up="(Placeholder: AI writing is off.)", why_it_matters="(Placeholder.)",
                   body=[s["summary"] for s in story["source_items"]], topics=[], image_query="")


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ai", action="store_true", help="skip Claude; placeholder articles")
    parser.add_argument("--per-section", type=int, default=STORIES_PER_SECTION)
    args = parser.parse_args()

    client = None
    if not args.no_ai:
        import anthropic
        client = anthropic.Anthropic(max_retries=6)
    costs = Costs()
    now = datetime.now(timezone.utc)
    stamp = f"{now:%Y-%m-%d-%H%M}"

    print("Fetching indicators...")
    indicators = fetch.fetch_indicators()

    print("Fetching feeds...")
    candidates = {key: fetch.gather_section(cfg["feeds"]) for key, cfg in SECTIONS.items()}

    print("Editor picking stories...")
    # Sections run in order so each editor knows what earlier sections already
    # took; otherwise a story like an AI lawsuit lands in both AI and Technology.
    all_picks, already = {}, []
    for key, items in candidates.items():
        if not items:
            picks = []
        elif client is None:
            picks = [Pick(source_ids=[it["id"]], working_title=it["title"]) for it in items[:args.per_section]]
        else:
            picks = pick_stories(client, costs, SECTIONS[key]["title"], items, args.per_section, already)
        all_picks[key] = picks
        already += [p.working_title for p in picks]

    stories, used = [], {key: set() for key in candidates}
    for key, picks in all_picks.items():
        by_id = {it["id"]: it for it in candidates[key]}
        for rank, p in enumerate(picks):
            used[key].update(p.source_ids)
            stories.append({
                "id": f"{stamp}-{key}{rank}-{slugify(p.working_title)}",
                "section": key,
                "section_title": SECTIONS[key]["title"],
                "rank": rank,
                "source_items": [by_id[i] for i in p.source_ids],
            })
    print(f"  {len(stories)} stories picked")

    print("Fetching full article text...")
    fetch.fetch_fulltexts([src for s in stories for src in s["source_items"]])

    print("Writing articles...")
    if client:
        written = write_articles(client, costs, stories, indicators)
    else:
        written = {s["id"][:64]: placeholder(s) for s in stories}

    articles = []
    for s in stories:
        art = written.get(s["id"][:64])
        if art is None:
            continue
        articles.append({
            **art.model_dump(),
            "id": s["id"],
            "section": s["section"],
            "section_title": s["section_title"],
            "rank": s["rank"],
            "sources": [{"name": x["source"], "url": x["url"]} for x in s["source_items"]],
            "wire_headline": s["source_items"][0]["title"],
            "wire_source": s["source_items"][0]["source"],
            "published": s["source_items"][0]["published"],
        })
    print(f"  {len(articles)} articles written")
    if not articles:
        sys.exit("No articles were written; leaving the site unchanged.")

    print("Writing front-page briefing...")
    briefing = write_briefing(client, costs, articles) if client else None

    if client:
        # Images are extras: if either step fails, the edition still publishes without them.
        print("Finding photos...")
        try:
            add_photos(client, costs, articles)
        except Exception as e:
            print(f"  ! photos skipped: {e}", file=sys.stderr)
        lead = articles[briefing.lead_index if briefing else 0]
        print("Drawing the cartoon...")
        try:
            comic = draw_cartoon(client, costs, lead)
        except Exception as e:
            print(f"  ! cartoon skipped: {e}", file=sys.stderr)
            comic = None
        if comic:
            lead["comic"] = comic

    # Headlines we didn't write up become "Elsewhere on the wire" links.
    wire = {key: [{"title": it["title"], "source": it["source"], "url": it["url"]}
                  for it in items if it["id"] not in used[key]][:8]
            for key, items in candidates.items()}

    data = {
        "generated_at": now.isoformat(),
        "model": MODEL if client else None,
        "cost_usd": round(costs.usd, 4),
        "indicators": indicators,
        "briefing": briefing.model_dump() if briefing else None,
        "articles": articles,
        "wire": wire,
    }
    archive = OUT_DIR / "data" / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    (OUT_DIR / "data" / "latest.json").write_text(payload, encoding="utf-8")
    (archive / f"{stamp}.json").write_text(payload, encoding="utf-8")
    write_site(data, OUT_DIR)
    print(f"Done. {len(articles)} articles. Estimated API cost this run: ${costs.usd:.3f}")


if __name__ == "__main__":
    main()
