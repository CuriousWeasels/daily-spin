# The Daily Spin (MVP)

A satirical news digest. Every 12 hours it:

1. Pulls headlines from free RSS feeds (`sources.py`) across Geopolitics, AI, Technology, and Markets.
2. Pulls key numbers (2Y/10Y yields, Fed funds, CPI, unemployment) from FRED's free CSV endpoint.
3. Sends each section's headlines to **Claude Haiku 5.5**, which picks the top 6 and rewrites them in a satirical tone (facts unchanged, every story links to its sources).
4. Writes a static page to `docs/index.html`.

## Run it locally

```
.venv\Scripts\python build.py --no-ai     # free: raw headlines only, to check feeds/layout
set ANTHROPIC_API_KEY=sk-ant-...           # PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
.venv\Scripts\python build.py             # full run with Claude
```

Then open `docs/index.html` in a browser.

## Paying for it with your Max plan API credits

Max 5x includes $100/month of API credits (Max 20x: $200). They are separate from your chat usage and expire at the end of each billing cycle.

1. Claim the credits into a Console organization (see "API credits for Max and Team plans" in the Claude docs).
2. In the Console, create an API key.
3. Optional but smart: set a monthly spend limit in the Console.

Estimated cost: ~4 Haiku calls per run, about $0.01 per run, so roughly **$0.50/month** at 2 runs a day.
Each run prints its estimated cost.

## Auto-update every 12 hours (GitHub Actions + GitHub Pages, both free)

1. Create a GitHub repo and push this folder.
2. Repo → Settings → Secrets and variables → Actions → New secret: `ANTHROPIC_API_KEY`.
3. Repo → Settings → Pages → Source: "Deploy from a branch", branch `main`, folder `/docs`.
4. Actions tab → "Update news" → Run workflow (to test right away).

`.github/workflows/update.yml` runs at 00:00 and 12:00 UTC, rebuilds, and commits `docs/`.
GitHub cron can be a few minutes late. That's normal.

## Files

- `sources.py`: feeds and indicators. Edit freely.
- `build.py`: fetch → rewrite → write. The satire style rules live in `SYSTEM_PROMPT`.
- `render.py`: the (intentionally ugly) HTML.
- `docs/data/archive/`: JSON of every run.
