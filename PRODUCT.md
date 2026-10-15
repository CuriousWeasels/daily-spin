# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

A curious generalist doing a quick daily catch-up, often on a phone (commute, coffee, lunch). They want to know what happened in the world in a few minutes and get a laugh while doing it. They are not specialists in geopolitics, AI, or markets.

## Product Purpose

The Daily Spin turns free, public news reporting into satirical articles that are funny and genuinely informative. A reader should leave knowing what happened and why it matters. Success: a reader can catch up on the day's important stories in minutes, understands them, and wants to come back for the next edition.

## Positioning

Funny and informative in equal measure: the jokes are how the reader learns. Every story is rewritten from real reporting by several outlets, with plain-language explanations of jargon ("Translation:" asides), a "Catch up" for context, and a "Why it matters" for consequences, and it links back to the original sources.

## Operating Context

- A new edition is generated automatically every 12 hours (00:00 and 12:00 UTC) by a GitHub Actions workflow and served as static files from GitHub Pages.
- Each edition: about 20 articles across four sections (Geopolitics, AI, Technology, Markets & Economy), a front-page lead, "5 Things in 60 Seconds", a "Number of the Day", a market data strip, and "Elsewhere on the wire" links to headlines that weren't written up.
- Readers arrive on the front page or directly on an article via a shared link.

## Capabilities and Constraints

- Stack: Python static generator (`build.py` pipeline, `render.py` produces all HTML/CSS/JS). No framework, no server. Pages must work as plain static files.
- Content is AI-written (Claude Sonnet 5.5) from RSS feeds plus full source text; numbers come from FRED. No images are available from sources (source photos are copyrighted and not used).
- Article length varies (roughly 450-800 words); headlines run long (often 10-15 words); deks are one sentence.
- Old editions' article pages stay online so shared links never break; `rerender.py` re-renders every page from saved data after design changes.
- Each article stores its original wire headline and source (`wire_headline`, `wire_source`).

## Brand Commitments

- Name: The Daily Spin. Tagline in use: "Real news. Unreal commentary."
- Voice: explainer comedy, deadpan, dry, never zany; punches up at the powerful, never mocks victims; restrained on tragedies.
- Must keep (in any form): "5 Things in 60 Seconds" with "Number of the Day", the market data strip, and the "Catch up" / "Why it matters" explainers on every article.
- Must disclose: satire written by AI from real reporting, with links to the original sources.
- Standing visual preference (owner's decision, 2026-10-15): a premium financial paper in the Wall Street Journal / Financial Times tradition, executed at their craft level. After exploring other worlds, the owner chose this over every alternative. The first, simpler newspaper version was not good enough; the bar is WSJ and FT themselves, with real gravitas, rich typography, a dense markets presence, and luxurious detail.

## Evidence on Hand

- Real editions in `docs/data/latest.json` and `docs/data/archive/` (articles, briefing, indicators, wire links).
- No logo, no photography, no illustrations, no testimonials or readership numbers. Do not invent any.

## Product Principles

1. Informative first, funny always: the reader must understand the story even if a joke misses.
2. A calm stage for a loud voice: long articles need comfortable, uncluttered reading, so the humor lives in the writing and in a few deliberate moments, not in visual chaos.
3. Minutes, not hours: the front page should let someone catch up fast, with depth one tap away.
4. Show the receipts: sources and original headlines stay visible; satire never hides where the facts came from.

## Accessibility & Inclusion

- Mobile-first reading comfort; respect `prefers-reduced-motion`.
- No specific standard confirmed beyond good WCAG AA practice.
