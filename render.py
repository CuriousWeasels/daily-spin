"""Static newspaper site: a WSJ/FT-style front page plus one page per article.

Motion, in order of importance:
  1. "The spin" (front page lead, once per visit): the wire headline is struck out
     and the satirical headline flips in word by word.
  2. Headline continuity: clicking a headline morphs it into the article title
     (cross-document View Transitions, where supported).
  3. Feedback: underline draw on hover, arrow nudge, focus rings.
  4. Market tape that pauses on hover/offscreen; reading-progress rule on articles.
All of it reduces to static final states under prefers-reduced-motion.
"""

import re
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

from sources import SECTIONS

FONTS = ("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900"
         "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400"
         "&family=Libre+Franklin:wght@400;500;600;700&display=swap")

ARROW = ('<svg class="arrow" width="14" height="10" viewBox="0 0 14 10" aria-hidden="true">'
         '<path d="M1 5h11M8.5 1.5 12 5l-3.5 3.5" fill="none" stroke="currentColor" stroke-width="1.6" '
         'stroke-linecap="round" stroke-linejoin="round"/></svg>')

CSS = """
:root {
  --ink:#141414; --ink-2:#3a3835; --muted:#5f5b55; --rule:#d9d2c5; --rule-strong:#141414;
  --paper:#fbf9f4; --box:#f2ede3; --accent:#9e1b1b; --accent-soft:#f1d9d2; --up:#0b6e3a;
  --serif:'Source Serif 4',Georgia,serif; --display:'Playfair Display',Georgia,serif;
  --sans:'Libre Franklin','Helvetica Neue',Arial,sans-serif;
  --ease-out:cubic-bezier(.16,1,.3,1);
}
* { box-sizing:border-box; }
html { scrollbar-color:#bdb4a5 var(--paper); -webkit-text-size-adjust:100%; }
body { margin:0; background:var(--paper); color:var(--ink); font-family:var(--serif); line-height:1.55;
       font-optical-sizing:auto; text-rendering:optimizeLegibility; }
::selection { background:var(--accent-soft); color:var(--ink); }
a { color:inherit; text-decoration:none; }
:focus-visible { outline:2px solid var(--accent); outline-offset:3px; border-radius:1px; }
.wrap { max-width:1200px; margin:0 auto; padding:0 16px; }
.meta { font-family:var(--sans); font-size:.75rem; color:var(--muted); letter-spacing:.01em; }
.meta .sec { color:var(--accent); font-weight:600; }

/* ---------- headline underline draw (hover feedback) ---------- */
.hl { background-image:linear-gradient(currentColor,currentColor); background-repeat:no-repeat;
      background-position:0 92%; background-size:0% 1.5px; -webkit-box-decoration-break:clone;
      box-decoration-break:clone; transition:background-size 320ms var(--ease-out); }
a:hover .hl, a:focus-visible .hl { background-size:100% 1.5px; }

/* ---------- masthead ---------- */
.topbar { font-family:var(--sans); font-size:.75rem; color:var(--muted); display:flex; justify-content:space-between;
          gap:12px; flex-wrap:wrap; padding:12px 0 0; }
.masthead { text-align:center; padding:14px 0 10px; }
.masthead h1 { font-family:var(--display); font-weight:900; font-size:clamp(2.8rem,8vw,5.4rem); margin:0;
               letter-spacing:-.02em; line-height:1; }
.masthead p { margin:8px 0 0; font-style:italic; color:var(--muted); font-size:1rem; }
nav.sections { font-family:var(--sans); font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:.09em;
               display:flex; justify-content:center; gap:28px; flex-wrap:wrap; padding:10px 0;
               border-top:1px solid var(--rule-strong); border-bottom:3px double var(--rule-strong); }
nav.sections a { position:relative; padding:2px 0; }
nav.sections a::after { content:""; position:absolute; left:0; right:0; bottom:-2px; height:2px; background:var(--accent);
                        transform:scaleX(0); transform-origin:left; transition:transform 260ms var(--ease-out); }
nav.sections a:hover::after, nav.sections a:focus-visible::after, nav.sections a[aria-current]::after { transform:scaleX(1); }

/* ---------- market tape ---------- */
.ticker { position:relative; overflow:hidden; border-bottom:1px solid var(--rule); font-family:var(--sans); font-size:.78rem;
          font-variant-numeric:tabular-nums; -webkit-mask-image:linear-gradient(90deg,transparent,#000 4%,#000 96%,transparent);
          mask-image:linear-gradient(90deg,transparent,#000 4%,#000 96%,transparent); }
.tape { display:flex; width:max-content; animation:tape 60s linear infinite; }
.tape-set { display:flex; }
.ticker:hover .tape, .ticker:focus-within .tape, .ticker.paused .tape { animation-play-state:paused; }
.tick { padding:9px 22px; white-space:nowrap; border-right:1px solid var(--rule); }
.tick b { margin:0 6px; font-weight:600; }
.tick .chg { font-weight:600; }
.up { color:var(--up); } .down { color:var(--accent); } .flat { color:var(--muted); }
.tick.src { color:var(--muted); }
@keyframes tape { to { transform:translateX(-50%); } }

/* ---------- front: lead + briefing ---------- */
.front { display:grid; grid-template-columns:minmax(0,2fr) minmax(0,1fr); gap:0; padding:28px 0 30px;
         border-bottom:1px solid var(--rule-strong); }
.lead { display:block; padding-right:32px; }
.headstack { display:grid; }
.headstack > * { grid-area:1/1; }
.lead h2 { font-family:var(--display); font-weight:800; font-size:clamp(2rem,4.4vw,3.4rem); line-height:1.08;
           letter-spacing:-.015em; margin:0 0 14px; text-wrap:balance; }
.wire-big { font-family:var(--display); font-weight:800; font-size:clamp(2rem,4.4vw,3.4rem); line-height:1.08;
            letter-spacing:-.015em; color:var(--ink-2); visibility:hidden; text-wrap:balance; }
.lead .dek { font-size:1.22rem; line-height:1.45; color:var(--ink-2); margin:0 0 14px; max-width:60ch; }
.lead .excerpt { font-size:1.05rem; margin:14px 0 14px; max-width:68ch; }
.wireline { font-family:var(--sans); font-size:.78rem; color:var(--muted); margin:0; }
.wireline s { text-decoration-color:var(--accent); text-decoration-thickness:1.5px; }
.more { font-family:var(--sans); font-size:.8rem; font-weight:700; color:var(--accent); display:inline-flex; align-items:center; gap:8px; }
.more .arrow, .card .arrow { transition:transform 220ms var(--ease-out); }
a:hover .more .arrow, a:focus-visible .more .arrow { transform:translateX(4px); }

aside.briefing { border-left:1px solid var(--rule); padding-left:28px; }
.briefing h2 { font-family:var(--sans); font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:.09em;
               margin:0 0 12px; padding-top:10px; border-top:2px solid var(--rule-strong); }
.briefing ol { list-style:none; counter-reset:t; margin:0 0 28px; padding:0; }
.briefing li { counter-increment:t; display:grid; grid-template-columns:28px 1fr; gap:4px; padding:10px 0;
               border-bottom:1px solid var(--rule); font-size:.97rem; line-height:1.45; }
.briefing li::before { content:counter(t); font-family:var(--display); font-weight:900; font-size:1.3rem; line-height:1.1;
                       color:var(--accent); font-variant-numeric:lining-nums; }
.big-number { font-family:var(--display); font-size:clamp(2.4rem,4vw,3.2rem); font-weight:900; line-height:1.05;
              letter-spacing:-.02em; margin:4px 0 8px; font-variant-numeric:lining-nums; }
.briefing p { margin:0; color:var(--ink-2); font-size:.97rem; }

/* ---------- sections ---------- */
.section { padding:30px 0 10px; border-bottom:1px solid var(--rule-strong); scroll-margin-top:12px; }
.section > h2 { font-family:var(--display); font-weight:800; font-size:1.65rem; letter-spacing:-.01em; margin:0 0 18px;
                padding-top:10px; border-top:3px solid var(--rule-strong); }
.grid { display:grid; grid-template-columns:minmax(0,2fr) minmax(0,1fr) minmax(0,1fr); }
.grid > * { padding:0 24px; }
.grid > *:first-child { padding-left:0; }
.grid > *:last-child { padding-right:0; }
.grid > * + * { border-left:1px solid var(--rule); }
.card { display:block; padding-bottom:16px; }
.card h3 { font-family:var(--display); font-weight:700; font-size:1.18rem; line-height:1.22; margin:0 0 8px; text-wrap:balance; }
.card.top h3 { font-size:clamp(1.5rem,2.4vw,1.95rem); line-height:1.14; }
.card p { margin:0 0 8px; font-size:.95rem; color:var(--ink-2); }
.card.top p.dek { font-size:1.05rem; }
.side-list .card + .card { border-top:1px solid var(--rule); padding-top:16px; }
.wire { margin:14px 0 18px; padding-top:12px; border-top:1px solid var(--rule); font-size:.86rem; line-height:1.6; }
.wire h3 { display:inline; font-family:var(--sans); font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; margin-right:6px; }
.wire a { color:var(--ink-2); text-decoration:underline; text-decoration-color:var(--rule); text-underline-offset:3px;
          transition:text-decoration-color 200ms; }
.wire a:hover { text-decoration-color:var(--ink); }
.wire span { color:var(--muted); }
.wire .sep { margin:0 6px; color:var(--rule); }

/* ---------- article page ---------- */
.mini { position:sticky; top:0; z-index:5; background:var(--paper); border-bottom:1px solid var(--rule-strong); }
.mini .wrap { display:flex; align-items:center; justify-content:space-between; gap:12px; padding-top:10px; padding-bottom:10px; }
.mini .logo { font-family:var(--display); font-weight:900; font-size:1.55rem; letter-spacing:-.01em; }
.mini nav.sections { border:0; padding:0; gap:18px; font-size:.75rem; }
.progress { position:absolute; left:0; right:0; bottom:-1px; height:2px; background:var(--accent);
            transform:scaleX(var(--p,0)); transform-origin:left; }
article.story { max-width:720px; margin:0 auto; padding:34px 0 10px; }
article.story h1 { font-family:var(--display); font-weight:800; font-size:clamp(2.1rem,5.2vw,3.3rem); line-height:1.08;
                   letter-spacing:-.015em; margin:0 0 16px; text-wrap:balance; }
article.story .dek { font-size:1.3rem; line-height:1.45; color:var(--ink-2); margin:0 0 14px; }
.byline { border-top:1px solid var(--rule); border-bottom:1px solid var(--rule); padding:10px 0; margin:18px 0 22px;
          display:flex; justify-content:space-between; flex-wrap:wrap; gap:6px; }
.callouts { display:grid; grid-template-columns:1fr 1fr; border-top:2px solid var(--rule-strong);
            border-bottom:1px solid var(--rule); margin-bottom:28px; }
.callout { padding:14px 0; font-size:.98rem; line-height:1.5; color:var(--ink-2); }
.callout + .callout { border-left:1px solid var(--rule); padding-left:20px; }
.callout:first-child { padding-right:20px; }
.callout h2 { font-family:var(--sans); font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.09em;
              color:var(--accent); margin:0 0 6px; }
.body p { font-size:1.14rem; line-height:1.68; margin:0 0 1.1em; }
.body p:first-child::first-letter { font-family:var(--display); float:left; font-size:4.1rem; line-height:.82;
                                    padding:7px 10px 0 0; font-weight:900; color:var(--ink); }
.sources { font-family:var(--sans); font-size:.82rem; color:var(--muted); border-top:1px solid var(--rule); padding-top:12px; margin-top:26px; }
.sources a { color:var(--ink); text-decoration:underline; text-decoration-color:var(--rule); text-underline-offset:3px; }
.sources a:hover { text-decoration-color:var(--ink); }
.related { border-top:3px double var(--rule-strong); margin-top:34px; padding:22px 0 34px; }
.related > h2 { font-family:var(--display); font-weight:800; font-size:1.45rem; margin:0 0 18px; }
.related .grid { grid-template-columns:repeat(4,minmax(0,1fr)); }

footer { border-top:1px solid var(--rule-strong); margin-top:10px; }
footer .wrap { display:flex; justify-content:space-between; gap:20px; flex-wrap:wrap; padding:22px 16px 44px; }
footer .logo { font-family:var(--display); font-weight:900; font-size:1.4rem; }
footer p { font-family:var(--sans); font-size:.76rem; color:var(--muted); max-width:62ch; margin:4px 0 0; line-height:1.55; }

/* ---------- motion 1: the spin (front lead, first visit) ---------- */
.spin-intro .wire-big { visibility:visible; animation:wire-out 380ms var(--ease-out) 900ms both; }
.spin-intro .wire-big span { background-image:linear-gradient(var(--accent),var(--accent)); background-repeat:no-repeat;
  background-position:0 56%; -webkit-box-decoration-break:clone; box-decoration-break:clone;
  animation:strike 480ms var(--ease-out) 260ms both; }
.spin-intro #lead-head .w { display:inline-block; transform-origin:50% 0; backface-visibility:hidden;
  animation:flip-in 560ms var(--ease-out) var(--d) both; }
@keyframes strike { from { background-size:0% .09em; } to { background-size:100% .09em; } }
@keyframes wire-out { to { opacity:0; transform:translateY(-.25em) rotateX(55deg); filter:blur(3px); } }
@keyframes flip-in { from { opacity:0; transform:perspective(600px) rotateX(-92deg); } 60% { opacity:1; }
  to { opacity:1; transform:perspective(600px) rotateX(0); } }

/* ---------- motion 2: headline continuity across pages ---------- */
@view-transition { navigation:auto; }
::view-transition-old(root) { animation:180ms ease-in both vt-fade-out; }
::view-transition-new(root) { animation:300ms var(--ease-out) 60ms both vt-fade-in; }
::view-transition-group(*) { animation-duration:460ms; animation-timing-function:var(--ease-out); }
@keyframes vt-fade-out { to { opacity:0; } }
@keyframes vt-fade-in { from { opacity:0; } }

@media (max-width:860px) {
  .front, .grid, .related .grid, .callouts { grid-template-columns:minmax(0,1fr); }
  .lead { padding-right:0; }
  aside.briefing { border-left:0; padding-left:0; margin-top:26px; }
  .grid > * { padding:0; }
  .grid > * + * { border-left:0; border-top:1px solid var(--rule); padding-top:16px; }
  .callout + .callout { border-left:0; border-top:1px solid var(--rule); padding-left:0; }
  .callout:first-child { padding-right:0; }
  .mini nav.sections { display:none; }
  .topbar .credit { display:none; }
  nav.sections { gap:18px; }
}

@media (prefers-reduced-motion:reduce) {
  @view-transition { navigation:none; }
  .tape { animation:none; flex-wrap:wrap; width:auto; }
  .tape [aria-hidden] { display:none; }
  .tape-set { flex-wrap:wrap; }
  .ticker { -webkit-mask-image:none; mask-image:none; }
  .hl { transition:none; }
  a:hover .hl, a:focus-visible .hl { background-size:100% 1.5px; }
  .more .arrow, nav.sections a::after { transition:none; }
}
"""

# First-visit gate for the spin. Runs in <head>, before paint; any failure leaves the final state.
INTRO_GATE = """<script>(function(){try{if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
if(sessionStorage.getItem('spun'))return;sessionStorage.setItem('spun','1');
document.documentElement.classList.add('spin-intro');}catch(e){}})();</script>"""

# Splits the lead headline into words right after it is parsed (still before first paint).
INTRO_SPLIT = """<script>(function(){var r=document.documentElement;if(!r.classList.contains('spin-intro'))return;
var h=document.getElementById('lead-head');if(!h||!document.querySelector('.wire-big')){r.classList.remove('spin-intro');return;}
var esc=function(s){return s.replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});};
var words=h.textContent.trim().split(/\\s+/),step=Math.min(32,420/words.length);
h.innerHTML=words.map(function(w,i){return'<span class="w" style="--d:'+Math.round(980+i*step)+'ms">'+esc(w)+'</span>';}).join(' ');
setTimeout(function(){r.classList.remove('spin-intro');},2400);})();</script>"""

# Tape pauses offscreen / in background tabs; article pages drive the reading-progress rule.
SITE_JS = """(function(){
var t=document.querySelector('.ticker');
if(t&&'IntersectionObserver'in window){new IntersectionObserver(function(e){t.classList.toggle('paused',!e[0].isIntersecting);}).observe(t);
document.addEventListener('visibilitychange',function(){t.classList.toggle('paused',document.hidden);});}
var p=document.querySelector('.progress'),a=document.querySelector('article.story');
if(p&&a){var queued=false,update=function(){queued=false;var r=a.getBoundingClientRect(),h=r.height-innerHeight;
p.style.setProperty('--p',Math.min(1,Math.max(0,h>0?-r.top/h:1)).toFixed(4));};
addEventListener('scroll',function(){if(!queued){queued=true;requestAnimationFrame(update);}},{passive:true});
addEventListener('resize',update);update();}
})();"""


def _when(iso: str | None) -> str:
    return datetime.fromisoformat(iso).strftime("%b %d, %Y %H:%M UTC") if iso else ""


def _vt(a: dict) -> str:
    """Shared view-transition name for an article's headline on every page it appears."""
    return "h-" + re.sub(r"[^a-z0-9-]", "", a["id"].lower())


def _hl(text: str, el_id: str = "") -> str:
    id_attr = f' id="{el_id}"' if el_id else ""
    return f'<span class="hl"{id_attr}>{escape(text)}</span>'


def _page(title: str, body: str, root: str, head_extra: str = "") -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#fbf9f4">
<title>{escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="{root}style.css">
{head_extra}
</head><body>{body}
<footer><div class="wrap"><div><a class="logo" href="{root}index.html">The Daily Spin</a>
<p>Satire written by AI from real reporting. The facts are meant to be accurate; the tone is not meant to be neutral.
Every article links to its original sources. Read them for the straight version.</p></div>
<p>A new edition every 12 hours.</p></div></footer>
<script src="{root}site.js" defer></script>
</body></html>"""


def _nav(root: str, front: bool, current: str = "") -> str:
    href = "#" if front else f"{root}index.html#"
    current_attr = ' aria-current="true"'
    links = "".join(
        f'<a href="{href}{k}"{current_attr if k == current else ""}>{escape(v["title"])}</a>'
        for k, v in SECTIONS.items())
    return f'<nav class="sections" aria-label="Sections">{links}</nav>'


def _link(a: dict, root: str) -> str:
    return f"{root}articles/{a['id']}.html"


def _read_time(a: dict) -> int:
    return max(1, round(sum(len(p.split()) for p in a["body"]) / 230))


def _card(a: dict, root: str, top: bool = False, show_section: bool = False) -> str:
    excerpt = f'<p>{escape(a["body"][0])}</p>' if top and a["body"] else ""
    sec = f'<span class="sec">{escape(a["section_title"])}</span> &middot; ' if show_section else ""
    return (f'<a class="card{" top" if top else ""}" href="{_link(a, root)}">'
            f'<h3 style="view-transition-name:{_vt(a)}">{_hl(a["headline"])}</h3>'
            f'<p class="dek">{escape(a["dek"])}</p>{excerpt}'
            f'<div class="meta">{sec}{_read_time(a)} min read</div></a>')


def _wire(items: list[dict], limit: int = 6) -> str:
    if not items:
        return ""
    links = '<span class="sep" aria-hidden="true">/</span>'.join(
        f'<a href="{escape(w["url"])}" target="_blank" rel="noopener">{escape(w["title"])}</a> <span>{escape(w["source"])}</span>'
        for w in items[:limit])
    return f'<div class="wire"><h3>Elsewhere on the wire</h3>{links}</div>'


def _ticker(indicators: list[dict]) -> str:
    if not indicators:
        return ""
    cells = []
    for i in indicators:
        c = i["change"]
        cls = "up" if c > 0 else "down" if c < 0 else "flat"
        sign = "+" if c > 0 else "−" if c < 0 else "±"
        cells.append(f'<span class="tick">{escape(i["label"])}<b>{i["value"]:.2f}{escape(i["unit"])}</b>'
                     f'<span class="chg {cls}">{sign}{abs(c):.2f}</span></span>')
    cells.append('<span class="tick src">Data: FRED, St. Louis Fed</span>')
    row = "".join(cells)
    # Several copies make one seamless loop wider than any screen; extras are hidden from assistive tech.
    copies = f'<div class="tape-set">{row}</div>' + "".join(
        f'<div class="tape-set" aria-hidden="true">{row}</div>' for _ in range(3))
    return f'<div class="ticker" aria-label="Market data"><div class="tape">{copies}</div></div>'


def _next_edition(iso: str) -> str:
    t = datetime.fromisoformat(iso)
    nxt = t.replace(hour=12, minute=0) if t.hour < 12 else (t + timedelta(days=1)).replace(hour=0, minute=0)
    return nxt.strftime("%H:%M UTC")


def render_front(data: dict) -> str:
    arts = data["articles"]
    b = data.get("briefing")
    lead = arts[b["lead_index"]] if b else arts[0]

    wire = lead.get("wire_headline")
    wire_big = f'<div class="wire-big" aria-hidden="true"><span>{escape(wire)}</span></div>' if wire else ""
    wire_line = (f'<p class="wireline">The wire said: <s>{escape(wire)}</s> ({escape(lead.get("wire_source", ""))})</p>'
                 if wire else "")
    lead_html = f"""<a class="lead" href="{_link(lead, '')}">
<div class="headstack">{wire_big}<h2 style="view-transition-name:{_vt(lead)}">{_hl(lead["headline"], "lead-head")}</h2></div>
{INTRO_SPLIT}
<p class="dek">{escape(lead["dek"])}</p>
{wire_line}
<p class="excerpt">{escape(lead["body"][0] if lead["body"] else "")}</p>
<span class="more">Continue reading {ARROW}</span>
<div class="meta" style="margin-top:10px"><span class="sec">{escape(lead["section_title"])}</span> &middot; {_read_time(lead)} min read</div>
</a>"""

    side = ""
    if b:
        things = "".join(f"<li><span>{escape(t)}</span></li>" for t in b["five_things"])
        n = b["number_of_the_day"]
        side = (f'<aside class="briefing" aria-label="Briefing"><h2>5 Things in 60 Seconds</h2><ol>{things}</ol>'
                f'<h2>Number of the Day</h2><div class="big-number">{escape(n["figure"])}</div>'
                f'<p>{escape(n["explanation"])}</p></aside>')

    sections = []
    for key, cfg in SECTIONS.items():
        sec = sorted((a for a in arts if a["section"] == key and a is not lead), key=lambda a: a["rank"])
        if not sec:
            continue
        top, rest = sec[0], sec[1:]
        half = (len(rest) + 1) // 2
        cols = "".join(f'<div class="side-list">{"".join(_card(a, "") for a in col)}</div>'
                       for col in (rest[:half], rest[half:]) if col)
        sections.append(f'<section class="section" id="{key}"><h2>{escape(cfg["title"])}</h2>'
                        f'<div class="grid">{_card(top, "", top=True)}{cols}</div>'
                        f'{_wire(data["wire"].get(key, []))}</section>')

    gen = data["generated_at"]
    byline = f"Written by {data['model']}" if data["model"] else "Placeholder text (AI writing off)"
    body = f"""<div class="wrap">
<div class="topbar"><span>{datetime.fromisoformat(gen):%A, %B %d, %Y}</span>
<span>Edition of {datetime.fromisoformat(gen):%H:%M} UTC &middot; next edition {_next_edition(gen)}<span class="credit"> &middot; {escape(byline)}</span></span></div>
<header class="masthead"><h1>The Daily Spin</h1><p>Real news. Unreal commentary.</p></header>
{_nav("", True)}
{_ticker(data["indicators"])}
<main>
<div class="front">{lead_html}{side}</div>
{"".join(sections)}
</main>
</div>"""
    return _page("The Daily Spin", body, "", INTRO_GATE)


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
    paras = "".join(f"<p>{escape(p)}</p>" for p in a["body"])
    first_by_outlet = {s["name"]: s["url"] for s in reversed(a["sources"])}
    sources = ", ".join(f'<a href="{escape(url)}" target="_blank" rel="noopener">{escape(name)}</a>'
                        for name, url in reversed(first_by_outlet.items()))
    wire = a.get("wire_headline")
    wire_line = (f'<p class="wireline">The wire said: <s>{escape(wire)}</s> ({escape(a.get("wire_source", ""))})</p>'
                 if wire else "")
    related = "".join(_card(r, root, show_section=True) for r in _related(a, data["articles"]))
    body = f"""<header class="mini"><div class="wrap"><a class="logo" href="{root}index.html">The Daily Spin</a>
{_nav(root, False, a["section"])}</div><div class="progress" aria-hidden="true"></div></header>
<div class="wrap">
<main>
<article class="story">
<h1 style="view-transition-name:{_vt(a)}">{escape(a["headline"])}</h1>
<p class="dek">{escape(a["dek"])}</p>
{wire_line}
<div class="byline meta"><span>By The Daily Spin Desk &middot; <span class="sec">{escape(a["section_title"])}</span></span>
<span>{_when(data["generated_at"])} &middot; {_read_time(a)} min read</span></div>
<div class="callouts"><section class="callout"><h2>Catch up</h2>{escape(a["catch_up"])}</section>
<section class="callout"><h2>Why it matters</h2>{escape(a["why_it_matters"])}</section></div>
<div class="body">{paras}</div>
<p class="sources">Satire based on reporting by {sources}. Read the originals for the straight version.</p>
</article>
<section class="related" aria-label="Related coverage"><h2>Related coverage</h2><div class="grid">{related}</div>
{_wire(data["wire"].get(a["section"], []), 8)}</section>
</main>
</div>"""
    return _page(f'{a["headline"]} | The Daily Spin', body, root)


def write_site(data: dict, out_dir: Path) -> None:
    (out_dir / "articles").mkdir(parents=True, exist_ok=True)
    (out_dir / "style.css").write_text(CSS, encoding="utf-8")
    (out_dir / "site.js").write_text(SITE_JS, encoding="utf-8")
    for a in data["articles"]:
        (out_dir / "articles" / f"{a['id']}.html").write_text(render_article(a, data), encoding="utf-8")
    (out_dir / "index.html").write_text(render_front(data), encoding="utf-8")
