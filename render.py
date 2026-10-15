"""Static newspaper site: a WSJ/FT-style front page plus one page per article."""

from datetime import datetime
from html import escape
from pathlib import Path

from sources import SECTIONS

FONTS = ("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900"
         "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400"
         "&family=Libre+Franklin:wght@400;600;700&display=swap")

CSS = """
:root { --ink:#121212; --muted:#5a5a5a; --rule:#d6d0c4; --paper:#fdfcf8; --accent:#9e1b1b; --box:#f3efe6; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font-family:'Source Serif 4',Georgia,serif; line-height:1.55; }
a { color:inherit; text-decoration:none; }
a:hover h2, a:hover h3, a:hover h4, .wire a:hover, .sources a:hover { text-decoration:underline; }
.wrap { max-width:1180px; margin:0 auto; padding:0 16px; }
.sans { font-family:'Libre Franklin',Arial,sans-serif; }
.topbar { font-family:'Libre Franklin',sans-serif; font-size:.75rem; color:var(--muted); display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; padding:10px 0 0; }
.masthead { text-align:center; padding:10px 0 6px; border-bottom:1px solid var(--ink); }
.masthead h1 { font-family:'Playfair Display',Georgia,serif; font-weight:900; font-size:clamp(2.6rem,7vw,4.6rem); margin:0; letter-spacing:-.5px; line-height:1.05; }
.masthead p { margin:4px 0 0; font-style:italic; color:var(--muted); }
.mini { display:flex; align-items:baseline; justify-content:space-between; flex-wrap:wrap; gap:8px; border-bottom:1px solid var(--ink); padding:12px 0 8px; }
.mini a.logo { font-family:'Playfair Display',serif; font-weight:900; font-size:1.8rem; }
nav { font-family:'Libre Franklin',sans-serif; font-size:.8rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; display:flex; justify-content:center; gap:22px; flex-wrap:wrap; padding:9px 0; border-bottom:3px double var(--ink); }
.mini nav { border:0; padding:0; gap:16px; }
.ticker { display:flex; gap:0; flex-wrap:wrap; border-bottom:1px solid var(--rule); font-family:'Libre Franklin',sans-serif; font-size:.78rem; }
.ticker div { padding:8px 16px 8px 0; margin-right:16px; border-right:1px solid var(--rule); }
.ticker b { margin:0 4px; }
.up { color:#0a7a3e; } .down { color:var(--accent); }
.kicker { font-family:'Libre Franklin',sans-serif; font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:var(--accent); }
.meta { font-family:'Libre Franklin',sans-serif; font-size:.75rem; color:var(--muted); }
.front { display:grid; grid-template-columns:2fr 1fr; gap:28px; padding:22px 0; border-bottom:1px solid var(--ink); }
.lead h2 { font-family:'Playfair Display',serif; font-size:clamp(1.8rem,4vw,2.7rem); line-height:1.12; margin:6px 0 10px; }
.dek { font-size:1.15rem; color:#333; margin:0 0 10px; }
.lead .excerpt { font-size:1.02rem; }
.more { font-family:'Libre Franklin',sans-serif; font-size:.8rem; font-weight:700; color:var(--accent); }
aside .box { background:var(--box); padding:16px 18px; margin-bottom:18px; border-top:3px solid var(--ink); }
aside h3 { font-family:'Libre Franklin',sans-serif; font-size:.85rem; text-transform:uppercase; letter-spacing:.06em; margin:0 0 8px; }
aside ol { margin:0; padding-left:20px; } aside li { margin-bottom:8px; font-size:.95rem; }
.big-number { font-family:'Playfair Display',serif; font-size:2.4rem; font-weight:900; line-height:1.1; }
.section { padding:20px 0 6px; border-bottom:1px solid var(--ink); }
.section > h2 { font-family:'Libre Franklin',sans-serif; font-size:.95rem; text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid var(--rule); padding-bottom:6px; margin:0 0 14px; }
.grid { display:grid; grid-template-columns:2fr 1fr 1fr; gap:24px; }
.card { padding-bottom:14px; }
.card h3 { font-family:'Playfair Display',serif; font-size:1.2rem; line-height:1.2; margin:4px 0 6px; }
.card.top h3 { font-size:1.7rem; }
.card p { margin:0 0 6px; font-size:.95rem; color:#333; }
.side-list .card { border-bottom:1px solid var(--rule); margin-bottom:12px; }
.wire { margin:10px 0 14px; font-size:.85rem; }
.wire b { font-family:'Libre Franklin',sans-serif; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; }
.wire a { color:#333; } .wire span { color:var(--muted); }
article.story { max-width:700px; margin:0 auto; padding:26px 0 10px; }
article.story h1 { font-family:'Playfair Display',serif; font-size:clamp(2rem,5vw,2.9rem); line-height:1.1; margin:8px 0 12px; }
article.story .dek { font-size:1.3rem; }
.byline { border-top:1px solid var(--rule); border-bottom:1px solid var(--rule); padding:8px 0; margin:14px 0 18px; }
.callouts { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:20px; }
.callout { background:var(--box); padding:12px 14px; font-size:.95rem; border-left:3px solid var(--accent); }
.callout b { display:block; font-family:'Libre Franklin',sans-serif; font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; margin-bottom:4px; }
.body p { font-size:1.12rem; margin:0 0 1.05em; }
.body p:first-child::first-letter { font-family:'Playfair Display',serif; float:left; font-size:3.6rem; line-height:.85; padding:6px 8px 0 0; font-weight:900; }
.sources { font-size:.85rem; color:var(--muted); border-top:1px solid var(--rule); padding-top:10px; margin-top:20px; }
.sources a { color:var(--ink); border-bottom:1px solid var(--rule); }
.related { border-top:3px double var(--ink); margin-top:26px; padding:16px 0 30px; }
.related > h2 { font-family:'Libre Franklin',sans-serif; font-size:.9rem; text-transform:uppercase; letter-spacing:.08em; margin:0 0 14px; }
.related .grid { grid-template-columns:repeat(4,1fr); }
footer { font-family:'Libre Franklin',sans-serif; font-size:.75rem; color:var(--muted); padding:20px 0 40px; text-align:center; }
@media (max-width:820px) {
  .front, .grid, .related .grid, .callouts { grid-template-columns:1fr; }
  .ticker { flex-wrap:nowrap; overflow-x:auto; white-space:nowrap; }
  .ticker div { padding-right:10px; margin-right:10px; }
}
"""


def _when(iso: str | None) -> str:
    return datetime.fromisoformat(iso).strftime("%b %d, %Y %H:%M UTC") if iso else ""


def _page(title: str, body: str, root: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="{root}style.css">
</head><body>{body}
<footer class="wrap">The Daily Spin is satire written by AI from real reporting. The facts are meant to be accurate; the tone is not meant to be neutral.
Always check the linked original reporting.</footer>
</body></html>"""


def _nav(root: str, front: bool) -> str:
    href = "#" if front else f"{root}index.html#"
    return "<nav>" + "".join(f'<a href="{href}{k}">{escape(v["title"])}</a>' for k, v in SECTIONS.items()) + "</nav>"


def _link(a: dict, root: str) -> str:
    return f"{root}articles/{a['id']}.html"


def _card(a: dict, root: str, top: bool = False, kicker: bool = False) -> str:
    k = f'<div class="kicker">{escape(a["section_title"])}</div>' if kicker else ""
    excerpt = f'<p>{escape(a["body"][0])}</p>' if top and a["body"] else ""
    return (f'<a class="card{" top" if top else ""}" href="{_link(a, root)}">{k}'
            f'<h3>{escape(a["headline"])}</h3><p>{escape(a["dek"])}</p>{excerpt}</a>')


def _wire(items: list[dict], limit: int = 6) -> str:
    if not items:
        return ""
    links = " &middot; ".join(
        f'<a href="{escape(w["url"])}" target="_blank" rel="noopener">{escape(w["title"])}</a> <span>({escape(w["source"])})</span>'
        for w in items[:limit])
    return f'<div class="wire"><b>Elsewhere on the wire:</b> {links}</div>'


def _ticker(indicators: list[dict]) -> str:
    if not indicators:
        return ""
    cells = []
    for i in indicators:
        cls, arrow = ("up", "&#9650;") if i["change"] > 0 else ("down", "&#9660;") if i["change"] < 0 else ("", "&ndash;")
        cells.append(f'<div>{escape(i["label"])}<b>{i["value"]:.2f}{escape(i["unit"])}</b>'
                     f'<span class="{cls}">{arrow} {abs(i["change"]):.2f}</span></div>')
    return f'<div class="ticker">{"".join(cells)}<div class="meta">FRED data</div></div>'


def render_front(data: dict) -> str:
    arts = data["articles"]
    b = data.get("briefing")
    lead = arts[b["lead_index"]] if b else arts[0]
    lead_html = (f'<a class="lead" href="{_link(lead, "")}"><div class="kicker">{escape(lead["section_title"])}</div>'
                 f'<h2>{escape(lead["headline"])}</h2><p class="dek">{escape(lead["dek"])}</p>'
                 f'<p class="excerpt">{escape(lead["body"][0] if lead["body"] else "")}</p>'
                 f'<span class="more">Continue reading &rarr;</span></a>')
    side = ""
    if b:
        things = "".join(f"<li>{escape(t)}</li>" for t in b["five_things"])
        n = b["number_of_the_day"]
        side = (f'<div class="box"><h3>5 Things in 60 Seconds</h3><ol>{things}</ol></div>'
                f'<div class="box"><h3>Number of the Day</h3><div class="big-number">{escape(n["figure"])}</div>'
                f'<p>{escape(n["explanation"])}</p></div>')

    sections = []
    for key, cfg in SECTIONS.items():
        sec = sorted((a for a in arts if a["section"] == key and a is not lead), key=lambda a: a["rank"])
        if not sec:
            continue
        top, rest = sec[0], sec[1:]
        half = (len(rest) + 1) // 2
        cols = [rest[:half], rest[half:]]
        side_cols = "".join(f'<div class="side-list">{"".join(_card(a, "") for a in col)}</div>' for col in cols)
        sections.append(f'<section class="section" id="{key}"><h2>{escape(cfg["title"])}</h2>'
                        f'<div class="grid">{_card(top, "", top=True)}{side_cols}</div>'
                        f'{_wire(data["wire"].get(key, []))}</section>')

    mode = f"Written by {data['model']}" if data["model"] else "PLACEHOLDER TEXT (AI writing off)"
    body = f"""<div class="wrap">
<div class="topbar"><span>{datetime.fromisoformat(data["generated_at"]):%A, %B %d, %Y}</span>
<span>Updated {_when(data["generated_at"])} &middot; new edition every 12 hours &middot; {escape(mode)}</span></div>
<header class="masthead"><h1>The Daily Spin</h1><p>Real news. Unreal commentary.</p></header>
{_nav("", True)}
{_ticker(data["indicators"])}
<div class="front">{lead_html}<aside>{side}</aside></div>
{"".join(sections)}
</div>"""
    return _page("The Daily Spin", body, "")


def _related(a: dict, arts: list[dict]) -> list[dict]:
    topics = set(a["topics"])
    scored = []
    for other in arts:
        if other is a:
            continue
        score = 2 * len(topics & set(other["topics"])) + (other["section"] == a["section"])
        scored.append((score, -other["rank"], other))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [o for _, _, o in scored[:4]]


def render_article(a: dict, data: dict) -> str:
    root = "../"
    words = sum(len(p.split()) for p in a["body"])
    paras = "".join(f"<p>{escape(p)}</p>" for p in a["body"])
    first_by_outlet = {s["name"]: s["url"] for s in reversed(a["sources"])}
    sources = ", ".join(f'<a href="{escape(url)}" target="_blank" rel="noopener">{escape(name)}</a>'
                        for name, url in reversed(first_by_outlet.items()))
    related = "".join(_card(r, root, kicker=True) for r in _related(a, data["articles"]))
    body = f"""<div class="wrap">
<div class="mini"><a class="logo" href="{root}index.html">The Daily Spin</a>{_nav(root, False)}</div>
<article class="story">
<div class="kicker">{escape(a["section_title"])}</div>
<h1>{escape(a["headline"])}</h1>
<p class="dek">{escape(a["dek"])}</p>
<div class="byline meta">By The Daily Spin Desk &middot; {_when(data["generated_at"])} &middot; {max(1, round(words / 230))} min read</div>
<div class="callouts"><div class="callout"><b>Catch up</b>{escape(a["catch_up"])}</div>
<div class="callout"><b>Why it matters</b>{escape(a["why_it_matters"])}</div></div>
<div class="body">{paras}</div>
<p class="sources">Satire based on reporting by {sources}. Read the originals for the straight version.</p>
</article>
<section class="related"><h2>Related coverage</h2><div class="grid">{related}</div>
{_wire(data["wire"].get(a["section"], []), 8)}</section>
</div>"""
    return _page(f'{a["headline"]} | The Daily Spin', body, root)


def write_site(data: dict, out_dir: Path) -> None:
    (out_dir / "articles").mkdir(parents=True, exist_ok=True)
    (out_dir / "style.css").write_text(CSS, encoding="utf-8")
    for a in data["articles"]:
        (out_dir / "articles" / f"{a['id']}.html").write_text(render_article(a, data), encoding="utf-8")
    (out_dir / "index.html").write_text(render_front(data), encoding="utf-8")
