---
version: 1
slug: "render-py"
primary_target: "render.py"
related_targets: []
---

# Surface brief: The Daily Spin front page and article pages

Scope: every page `render.py` generates (front page `docs/index.html`, article pages `docs/articles/*.html`). Visitor mode: Read.
Audience and job: a generalist catching up on a phone or laptop in minutes; depth one tap away.
Proof and content: real editions in `docs/data/` (20 articles, briefing, FRED indicators, wire links). No photography.
Constraints: static files, mobile-first comfort, prefers-reduced-motion respected, AI-satire disclosure and sources always visible.

## Direction contract

THESIS: A premium financial daily in the WSJ/FT tradition, played straight at their craft level, so the deadpan satire lands harder. It refuses the generic news-portal card grid and the thin first-draft broadsheet.

OWN-WORLD: Warm financial-pink newsprint ground, near-black ink, claret as the only accent and oxford blue for data. A sharp transitional serif carries the headlines and text, Franklin-style gothic carries labels and figures. Hairline column rules and a heavy-light double rule under the masthead. A markets band of real FRED figures with drawn sparklines.

STORY: The reader sees the edition's gravity, catches up through the "What's News" briefing column, reads the lead, and dives into any section; articles read like a quality paper with the receipts shown.

FIRST VIEWPORT: Utility line, centred masthead with edition line, section nav, markets band with five figures and sparklines. Below it three columns: "What's News" (5 Things) narrow left, the lead with a large headline, standfirst, struck wire headline and opening paragraph centre, Number of the Day and top stories right.

FORM: The category standard (premium financial paper), owner-pinned after two re-rolls; seed key afdac8b7. Signature motion: an edition-opening sequence (masthead rules draw, lead headline unmasks line by line, sparklines plot) plus headline-to-title view transitions.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
