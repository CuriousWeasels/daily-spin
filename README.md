# The Daily Spin

A satirical but informative newspaper, rebuilt every 12 hours from free news sources and written by Claude Sonnet 5.5.
Live at https://curiousweasels.github.io/daily-spin/

## How a new edition is made

1. **Fetch.** Headlines from free RSS feeds (`sources.py`) plus key numbers from FRED (yields, Fed funds, CPI, unemployment).
2. **Editor** (1 Sonnet call per section). Picks the top 5 stories and groups outlets covering the same event.
3. **Research.** Downloads the full text of each story's 2-3 source articles. Sites that block this fall back to the RSS blurb.
4. **Writer** (Message Batches API, half price). One full article per story with a headline, dek, "Catch up", "Why it matters", body, and topic tags.
5. **Briefing** (1 call). Picks the front-page lead and writes "5 Things in 60 Seconds" and the "Number of the Day".
6. **Photos** (1 call). Each article proposes a photo search; `images.py` finds openly licensed candidates on Wikimedia Commons (Openverse as fallback; CC BY, CC BY-SA, CC0 and public domain only), and Claude picks one or none. Photos are labeled illustrative, with credits under them and in a Photo credits list.
7. **Cartoon** (1 call). Sonnet draws a single-panel editorial cartoon for the lead story as SVG (symbols only, never real people). It is sanitized and saved to `docs/comics/`. If drawing fails, the edition still publishes.
8. **Render.** Front page (`docs/index.html`) plus one page per article (`docs/articles/`), each with related coverage at the bottom.

## Changing the design

All markup, styles, and motion live in `render.py`. After editing it, run `.venv\Scripts\python rerender.py` to rebuild every page from the saved data (no API calls, free), then commit `docs/`. The visual system is documented in `DESIGN.md`.

Fonts are self-hosted in `docs/fonts/`. To change weights or widths, edit `CSS_URL` in `get_fonts.py` and run `.venv\Scripts\python get_fonts.py`.

## Changing the voice

All writing instructions live in `prompts.py`. The style is "explainer comedy": plain fact first, "Translation:" asides for jargon, humor that comes from how things actually work, and strict no-invented-facts rules.

## Running locally

```
.venv\Scripts\python build.py --no-ai            # free: placeholder text, for layout only
$env:ANTHROPIC_API_KEY="sk-ant-..."               # PowerShell
.venv\Scripts\python build.py --per-section 2    # cheap test (8 articles)
.venv\Scripts\python build.py                    # full edition (20 articles)
```

Every run prints its estimated API cost.

## Costs and knobs (in `build.py`)

- `MODEL`: `claude-sonnet-5-5`. Switch to `claude-haiku-5-5` for about 1/20 the cost, with flatter jokes.
- `STORIES_PER_SECTION`: 5, so 20 articles per edition.
- `EFFORT`: `medium`. `low` is cheaper; `high` thinks harder.

Your Max plan's monthly API credits pay for this ($100 on Max 5x, $200 on Max 20x). They are claimed into a Console organization and reset each billing cycle. Set a spend limit on the workspace in the Console as a safety net.

## Auto-update (GitHub Actions + Pages)

`.github/workflows/update.yml` runs at 00:00 and 12:00 UTC, builds, and commits `docs/`, which GitHub Pages serves.
To run it right away: Actions tab → "Update news" → Run workflow.
The API key is the repo secret `ANTHROPIC_API_KEY`. To replace an expired key:
`gh secret set ANTHROPIC_API_KEY --repo CuriousWeasels/daily-spin`
