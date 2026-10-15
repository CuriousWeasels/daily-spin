"""Turn the build data into a single static HTML page. Deliberately plain."""

from datetime import datetime
from html import escape


def _when(iso: str | None) -> str:
    if not iso:
        return ""
    return datetime.fromisoformat(iso).strftime("%b %d, %H:%M UTC")


def _indicators(indicators: list[dict]) -> str:
    if not indicators:
        return ""
    cells = []
    for i in indicators:
        arrow = "&#9650;" if i["change"] > 0 else "&#9660;" if i["change"] < 0 else "&ndash;"
        cells.append(
            f'<div class="ind"><span class="lbl">{escape(i["label"])}</span>'
            f'<b>{i["value"]:.2f}{escape(i["unit"])}</b>'
            f'<small>{arrow} {abs(i["change"]):.2f} &middot; {escape(i["as_of"])}</small></div>'
        )
    return f'<div class="inds">{"".join(cells)}</div><p class="note">Data: FRED, St. Louis Fed</p>'


def _story(s: dict) -> str:
    links = ", ".join(
        f'<a href="{escape(src["url"])}" target="_blank" rel="noopener">{escape(src["name"])}</a>'
        for src in s["sources"]
    )
    return (
        f'<article><h3>{escape(s["headline"])}</h3>'
        f'<p>{escape(s["summary"])}</p>'
        f'<p class="meta">Based on reporting by {links} &middot; {_when(s.get("published"))}</p></article>'
    )


def render_site(data: dict) -> str:
    nav = " | ".join(f'<a href="#{s["key"]}">{escape(s["title"])}</a>' for s in data["sections"])
    body = []
    for sec in data["sections"]:
        extra = _indicators(data["indicators"]) if sec["key"] == "markets" else ""
        stories = "".join(_story(s) for s in sec["stories"]) or "<p>No stories this cycle.</p>"
        body.append(f'<section id="{sec["key"]}"><h2>{escape(sec["title"])}</h2>{extra}{stories}</section>')

    mode = f"Rewritten by {data['model']}" if data["model"] else "RAW HEADLINES (AI rewrite off)"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Daily Spin</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 760px; margin: 0 auto; padding: 16px; line-height: 1.5; color: #111; background: #fff; }}
  header {{ border-bottom: 3px double #111; margin-bottom: 8px; }}
  h1 {{ margin: 0; font-size: 2.2rem; }}
  h2 {{ border-bottom: 1px solid #ccc; margin-top: 2rem; }}
  h3 {{ margin-bottom: 4px; }}
  article {{ margin-bottom: 1.2rem; }}
  .meta, .note, .tag {{ font-family: sans-serif; font-size: .8rem; color: #666; }}
  .inds {{ display: flex; flex-wrap: wrap; gap: 8px; font-family: sans-serif; }}
  .ind {{ border: 1px solid #ddd; padding: 6px 10px; display: flex; flex-direction: column; min-width: 110px; }}
  .ind .lbl {{ font-size: .75rem; color: #666; }}
  .ind small {{ color: #888; font-size: .7rem; }}
  nav {{ font-family: sans-serif; font-size: .9rem; margin: 8px 0; }}
</style></head>
<body>
<header><h1>The Daily Spin</h1>
<p class="tag">Real news, unreal commentary. Satire based on actual reporting; follow the source links for the straight version.</p></header>
<nav>{nav}</nav>
<p class="meta">Updated {_when(data["generated_at"])} &middot; refreshes every 12 hours &middot; {escape(mode)}</p>
{"".join(body)}
</body></html>
"""
