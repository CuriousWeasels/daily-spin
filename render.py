"""Static site in the premium financial-paper tradition: a front page plus one page per article.

Motion, in order of importance:
  1. Edition opening (front page, once per visit): the masthead rules draw out from the
     centre, the lead headline is pulled line by line like plates from the press, and the
     market sparklines plot themselves.
  2. Headline continuity: a headline morphs into the article title (cross-document
     View Transitions, where supported).
  3. Feedback: underline draw on hover, arrow nudge, focus rings, reading-progress rule.
Every effect resolves to its final state under prefers-reduced-motion, and the page is
complete without JavaScript.
"""

import math
import re
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

from sources import SECTIONS

FONTS = ("https://fonts.googleapis.com/css2?family=Noto+Serif+Display:ital,wdth,wght@0,62.5..100,500..900;1,62.5..100,400..600"
         "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400..600"
         "&family=Libre+Franklin:wght@400..800&display=swap")

ARROW = ('<svg class="arrow" width="15" height="10" viewBox="0 0 15 10" aria-hidden="true">'
         '<path d="M1 5h12M9 1.2 12.8 5 9 8.8" fill="none" stroke="currentColor" stroke-width="1.5" '
         'stroke-linecap="round" stroke-linejoin="round"/></svg>')

CSS = """
:root {
  --paper:#fcf0e4; --paper-2:#f6e3d2; --ink:#1c1714; --ink-2:#3d3530; --muted:#6a5e57;
  --rule:#dfc8b5; --rule-strong:#1c1714; --claret:#8c1f3c; --data:#1f4e86; --up:#0b6b3c; --down:#a8231c;
  --display:'Noto Serif Display',Georgia,serif; --serif:'Source Serif 4',Georgia,serif;
  --sans:'Libre Franklin','Franklin Gothic Medium','Arial Narrow',Arial,sans-serif;
  --ease:cubic-bezier(.16,1,.3,1);
}
* { box-sizing:border-box; }
html { scrollbar-color:#cdb29d var(--paper); -webkit-text-size-adjust:100%; }
body { margin:0; background:var(--paper); color:var(--ink); font-family:var(--serif); font-size:17px; line-height:1.55;
       font-optical-sizing:auto; text-rendering:optimizeLegibility; -webkit-font-smoothing:antialiased; }
::selection { background:#efcfc0; color:var(--ink); }
a { color:inherit; text-decoration:none; }
:focus-visible { outline:2px solid var(--claret); outline-offset:3px; }
.wrap { max-width:1260px; margin:0 auto; padding:0 20px; }
.meta { font-family:var(--sans); font-size:.78rem; color:var(--muted); font-variant-numeric:tabular-nums; }
.sec { color:var(--claret); font-weight:700; }
.up { color:var(--up); } .down { color:var(--down); } .flat { color:var(--muted); }

/* headline underline draw */
.hl { background:linear-gradient(currentColor,currentColor) no-repeat 0 94% / 0% 1px;
      -webkit-box-decoration-break:clone; box-decoration-break:clone; transition:background-size 360ms var(--ease); }
a:hover .hl, a:focus-visible .hl { background-size:100% 1px; }
.arrow { transition:transform 240ms var(--ease); }
a:hover .arrow, a:focus-visible .arrow { transform:translateX(4px); }

/* ---------- masthead ---------- */
.utility { display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; padding:12px 0 0;
           font-family:var(--sans); font-size:.75rem; color:var(--muted); font-variant-numeric:tabular-nums; }
.utility b { color:var(--ink); font-weight:600; }
.utility .narrow { display:none; }
.masthead { display:grid; grid-template-columns:minmax(0,1fr) auto minmax(0,1fr); align-items:center; gap:28px; padding:14px 0 0; }
.masthead h1 { margin:0; font-family:var(--display); font-weight:900; font-stretch:semi-condensed; text-transform:uppercase;
               font-size:clamp(2.7rem,6.6vw,5.4rem); line-height:.95; letter-spacing:-.012em; word-spacing:.06em; white-space:nowrap; }
.masthead h1 .the { font-style:italic; font-weight:500; text-transform:none; font-size:.42em; letter-spacing:0;
                    vertical-align:.95em; margin-right:.16em; }
.ear { font-family:var(--sans); font-size:.75rem; line-height:1.5; color:var(--muted); font-variant-numeric:tabular-nums;
       border-top:1px solid var(--rule-strong); border-bottom:1px solid var(--rule-strong); padding:8px 0; max-width:220px; }
.ear b { display:block; color:var(--ink); font-weight:700; font-size:.82rem; }
.ear.right { justify-self:end; text-align:right; }
.motto { display:flex; align-items:center; gap:18px; justify-content:center; margin:10px 0 0;
         font-family:var(--display); font-style:italic; font-weight:400; font-size:1.02rem; color:var(--ink-2); }
.motto::before, .motto::after { content:""; height:1px; width:min(18vw,170px); background:var(--rule); }
.double { margin-top:14px; height:5px; border-top:3px solid var(--rule-strong); border-bottom:1px solid var(--rule-strong);
          transform-origin:center; }
nav.sections { display:flex; justify-content:center; gap:30px; flex-wrap:wrap; padding:10px 0;
               border-bottom:1px solid var(--rule-strong); font-family:var(--sans); font-size:.8rem; font-weight:600;
               letter-spacing:.06em; text-transform:uppercase; }
nav.sections a { position:relative; padding:3px 0; white-space:nowrap; }
nav.sections a::after { content:""; position:absolute; left:0; right:0; bottom:-1px; height:2px; background:var(--claret);
                        transform:scaleX(0); transform-origin:left; transition:transform 280ms var(--ease); }
nav.sections a:hover::after, nav.sections a:focus-visible::after, nav.sections a[aria-current]::after { transform:scaleX(1); }

/* ---------- markets band ---------- */
.markets { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); border-bottom:1px solid var(--rule-strong);
           background:var(--paper-2); }
.mk { padding:9px 14px 8px; font-family:var(--sans); font-variant-numeric:tabular-nums; border-left:1px solid var(--rule); }
.mk:nth-child(5n+1) { border-left:0; }
.mk:nth-child(n+6) { border-top:1px solid var(--rule); }
.mk .top { display:flex; justify-content:space-between; gap:8px; font-size:.72rem; }
.mk .name { font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-2); white-space:nowrap; }
.mk .asof { color:var(--muted); white-space:nowrap; }
.mk .fig { display:flex; justify-content:space-between; align-items:baseline; gap:8px; margin-top:1px; }
.mk .val { font-size:1.15rem; font-weight:700; letter-spacing:-.01em; }
.mk .chg { font-size:.8rem; font-weight:600; }
.sp { position:relative; display:block; height:22px; margin-top:3px; }
.sp svg { position:absolute; inset:0; width:100%; height:100%; overflow:visible; }
.spark { fill:none; stroke:var(--data); stroke-width:1.5; vector-effect:non-scaling-stroke; stroke-linejoin:round; }
.dot { position:absolute; width:5px; height:5px; border-radius:50%; background:var(--data); transform:translate(-50%,-50%); }

/* ---------- front page ---------- */
.front { display:grid; grid-template-columns:250px minmax(0,1fr) 290px; padding:26px 0 30px; }
.front > * + * { border-left:1px solid var(--rule); }
.whats { padding-right:22px; }
.lead { display:block; padding:0 30px; }
.rail { padding-left:22px; }
.col-head { font-family:var(--sans); font-size:.78rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase;
            border-top:3px solid var(--rule-strong); padding-top:8px; margin:0 0 12px; }
.whats ol { list-style:none; margin:0; padding:0; }
.whats li { position:relative; padding:0 0 12px 16px; margin-bottom:12px; border-bottom:1px solid var(--rule);
            font-size:.95rem; line-height:1.45; }
.whats li:last-child { border-bottom:0; }
.whats li::before { content:""; position:absolute; left:0; top:.52em; width:7px; height:7px; background:var(--claret); }
.lead h2 { font-family:var(--display); font-weight:700; font-stretch:condensed; font-size:clamp(2.1rem,3.9vw,3.5rem);
           line-height:1.03; letter-spacing:-.008em; margin:0 0 14px; text-wrap:balance; }
.standfirst { font-size:1.22rem; line-height:1.45; color:var(--ink-2); margin:0 0 12px; }
.wireline { font-family:var(--sans); font-size:.8rem; color:var(--muted); margin:0 0 14px; line-height:1.45; }
.wireline s { text-decoration-color:var(--claret); text-decoration-thickness:1.5px; color:var(--ink-2); }
.byline { font-family:var(--sans); font-size:.78rem; color:var(--muted); padding:9px 0; margin:0 0 16px;
          border-top:1px solid var(--rule); border-bottom:1px solid var(--rule); display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; }
.byline b { color:var(--ink); font-weight:600; }
.lead .excerpt { columns:2 260px; column-gap:28px; column-rule:1px solid var(--rule); }
.lead .excerpt p { margin:0 0 .9em; font-size:1.04rem; line-height:1.62; }
.more { display:inline-flex; align-items:center; gap:8px; font-family:var(--sans); font-size:.8rem; font-weight:700;
        color:var(--claret); margin-top:4px; }
.rail .number { padding-bottom:18px; margin-bottom:18px; border-bottom:1px solid var(--rule); }
.big { font-family:var(--display); font-weight:800; font-stretch:semi-condensed; font-size:clamp(2.6rem,4vw,3.5rem);
       line-height:1; letter-spacing:-.01em; color:var(--claret); margin:6px 0 10px; font-variant-numeric:lining-nums; }
.rail .number p { margin:0; font-size:.95rem; line-height:1.5; color:var(--ink-2); }
.story { display:block; padding:0 0 14px; margin:0 0 14px; border-bottom:1px solid var(--rule); }
.story:last-child { border-bottom:0; margin-bottom:0; }
.story h3 { font-family:var(--serif); font-weight:700; font-size:1.14rem; line-height:1.25; letter-spacing:-.005em;
            margin:0 0 6px; text-wrap:balance; }
.story p { margin:0 0 6px; font-size:.95rem; line-height:1.45; color:var(--ink-2); }

/* ---------- sections ---------- */
.section { padding:22px 0 8px; scroll-margin-top:16px; }
.section-head { display:flex; align-items:baseline; justify-content:space-between; gap:16px; border-top:3px solid var(--rule-strong);
                padding-top:8px; margin-bottom:18px; }
.section-head h2 { margin:0; font-family:var(--display); font-weight:800; font-stretch:semi-condensed; font-size:1.9rem; line-height:1.1; }
.grid { display:grid; grid-template-columns:minmax(0,3fr) minmax(0,2fr); }
.grid.markets-grid { grid-template-columns:minmax(0,2fr) minmax(0,1.3fr) minmax(0,1.7fr); }
.grid > * { padding:0 24px; }
.grid > *:first-child { padding-left:0; }
.grid > *:last-child { padding-right:0; }
.grid > * + * { border-left:1px solid var(--rule); }
.story.top h3 { font-family:var(--display); font-size:clamp(1.6rem,2.4vw,2.1rem); line-height:1.08; font-stretch:condensed; letter-spacing:-.008em; }
.story.top p.standfirst { font-size:1.06rem; color:var(--ink-2); }
.wire { padding:12px 0 18px; border-top:1px solid var(--rule); margin-top:6px; font-size:.9rem; line-height:1.6; }
.wire h3 { display:inline; margin:0 8px 0 0; font-family:var(--sans); font-size:.75rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; }
.wire a { color:var(--ink-2); text-decoration:underline; text-decoration-color:var(--rule); text-underline-offset:3px; transition:text-decoration-color 200ms; }
.wire a:hover { text-decoration-color:var(--ink); }
.wire .src { font-family:var(--sans); font-size:.75rem; color:var(--muted); }
.wire .sep { display:inline-block; width:4px; height:4px; background:var(--rule); vertical-align:middle; margin:0 10px; }

/* markets table */
.mtable { width:100%; border-collapse:collapse; font-family:var(--sans); font-size:.82rem; font-variant-numeric:tabular-nums; }
.mtable caption { text-align:left; }
.mtable th { font-size:.7rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--muted);
             text-align:right; padding:0 0 6px 8px; border-bottom:1px solid var(--rule-strong); }
.mtable th:first-child, .mtable td:first-child { text-align:left; padding-left:0; }
.mtable td { padding:7px 0 7px 8px; border-bottom:1px solid var(--rule); text-align:right; white-space:nowrap; }
.mtable td:first-child { font-weight:600; color:var(--ink); }
.mtable td.trend { width:64px; }
.mtable .sp { height:16px; margin:0; }
.table-note { margin-top:8px; }

/* ---------- article ---------- */
.topbar { position:sticky; top:0; z-index:5; background:var(--paper); border-bottom:1px solid var(--rule-strong); }
.topbar .wrap { display:flex; align-items:center; justify-content:space-between; gap:16px; padding-top:10px; padding-bottom:10px; }
.topbar .logo { font-family:var(--display); font-weight:900; font-stretch:semi-condensed; font-size:1.45rem; text-transform:uppercase; letter-spacing:-.005em; }
.topbar nav.sections { border:0; padding:0; gap:20px; font-size:.75rem; }
.progress { position:absolute; left:0; right:0; bottom:-1px; height:2px; background:var(--claret);
            transform:scaleX(var(--p,0)); transform-origin:left; }
article.piece { max-width:740px; margin:0 auto; padding:38px 0 8px; }
article.piece h1 { font-family:var(--display); font-weight:700; font-stretch:condensed; font-size:clamp(2.3rem,5.4vw,3.7rem);
                   line-height:1.03; letter-spacing:-.008em; margin:0 0 16px; text-wrap:balance; }
article.piece .standfirst { font-size:1.32rem; }
.explain { display:grid; grid-template-columns:1fr 1fr; border-top:3px solid var(--rule-strong); border-bottom:1px solid var(--rule);
           margin:0 0 30px; }
.explain section { padding:12px 0 14px; font-size:1rem; line-height:1.5; color:var(--ink-2); }
.explain section + section { border-left:1px solid var(--rule); padding-left:20px; }
.explain section:first-child { padding-right:20px; }
.explain h2 { margin:0 0 6px; font-family:var(--sans); font-size:.75rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; color:var(--claret); }
.chart { margin:0 0 30px; padding:12px 0 10px; border-top:1px solid var(--rule-strong); border-bottom:1px solid var(--rule); }
.chart figcaption { font-family:var(--sans); font-size:.85rem; color:var(--muted); margin-bottom:14px; }
.chart figcaption b { display:block; font-family:var(--serif); font-size:1.15rem; color:var(--ink); }
.plot { position:relative; height:200px; margin-left:46px; margin-right:64px; }
.plot svg { position:absolute; inset:0; width:100%; height:100%; overflow:visible; }
.plot .grid-line { stroke:var(--rule); stroke-width:1; vector-effect:non-scaling-stroke; }
.plot .line { fill:none; stroke:var(--data); stroke-width:2.25; vector-effect:non-scaling-stroke; stroke-linejoin:round; }
.plot .yt { position:absolute; left:-46px; width:38px; text-align:right; transform:translateY(-50%);
            font-family:var(--sans); font-size:.72rem; color:var(--muted); font-variant-numeric:tabular-nums; }
.plot .dot { width:9px; height:9px; border:2px solid var(--paper); box-sizing:content-box; }
.plot .endlab { position:absolute; transform:translate(12px,-50%); font-family:var(--sans); font-size:.85rem; font-weight:700;
                color:var(--data); white-space:nowrap; font-variant-numeric:tabular-nums; }
.xaxis { display:flex; justify-content:space-between; margin:6px 64px 0 46px; font-family:var(--sans); font-size:.72rem; color:var(--muted); }
.chart .meta { margin:10px 0 0; }
.body p { font-size:1.16rem; line-height:1.72; margin:0 0 1.1em; max-width:68ch; }
.body p:first-child::first-letter { font-family:var(--display); font-weight:800; float:left; font-size:4.3rem; line-height:.8;
                                    padding:8px 10px 0 0; color:var(--ink); }
.sources { font-family:var(--sans); font-size:.82rem; color:var(--muted); border-top:1px solid var(--rule); padding-top:12px; margin-top:26px; line-height:1.6; }
.sources a { color:var(--ink); text-decoration:underline; text-decoration-color:var(--rule); text-underline-offset:3px; }
.sources a:hover { text-decoration-color:var(--ink); }
.related { border-top:3px solid var(--rule-strong); margin-top:36px; padding:10px 0 30px; }
.related .section-head { border-top:0; padding-top:0; }
.related .grid { grid-template-columns:repeat(4,minmax(0,1fr)); }

footer { border-top:1px solid var(--rule-strong); margin-top:6px; }
footer .wrap { display:grid; grid-template-columns:auto 1fr; gap:28px; padding-top:22px; padding-bottom:44px; align-items:start; }
footer .logo { font-family:var(--display); font-weight:900; font-stretch:semi-condensed; font-size:1.3rem; text-transform:uppercase; }
footer p { margin:0; font-family:var(--sans); font-size:.78rem; color:var(--muted); line-height:1.6; max-width:70ch; }

/* ---------- motion 1: edition opening ---------- */
.edition-open .double { animation:rule-out 760ms var(--ease) 120ms both; }
.edition-open .lead h2 { visibility:hidden; }
.edition-open.lines-ready .lead h2 { visibility:visible; }
.lines-ready .lead h2 .ln { display:block; animation:plate 760ms var(--ease) calc(240ms + var(--i) * 120ms) both; }
.edition-open .lead .standfirst, .edition-open .lead .wireline { animation:settle 600ms var(--ease) 700ms both; }
.edition-open .spark { stroke-dasharray:1; animation:plot 1100ms var(--ease) var(--d,300ms) both; }
.edition-open .markets .dot { animation:settle 300ms ease-out calc(var(--d,300ms) + 900ms) both; }
@keyframes rule-out { from { transform:scaleX(0); } }
@keyframes plate { from { clip-path:inset(0 0 100% 0); transform:translateY(.18em); } to { clip-path:inset(0 0 -10% 0); transform:none; } }
@keyframes settle { from { opacity:0; } }
@keyframes plot { from { stroke-dashoffset:1; } to { stroke-dashoffset:0; } }

/* ---------- motion 2: headline continuity ---------- */
@view-transition { navigation:auto; }
::view-transition-old(root) { animation:160ms ease-in both vt-out; }
::view-transition-new(root) { animation:300ms var(--ease) 40ms both vt-in; }
::view-transition-group(*) { animation-duration:480ms; animation-timing-function:var(--ease); }
@keyframes vt-out { to { opacity:0; } }
@keyframes vt-in { from { opacity:0; } }

@media (max-width:1060px) {
  .masthead { grid-template-columns:1fr; justify-items:center; }
  .ear { display:none; }
  .utility .narrow { display:inline; }
  .front { grid-template-columns:minmax(0,1fr) 270px; }
  .front > .whats { grid-column:1 / -1; order:2; padding:22px 0 0; margin-top:22px; border-left:0; border-top:1px solid var(--rule); }
  .lead { padding-left:0; }
  .whats ol { columns:2 280px; column-gap:28px; }
  .whats li { break-inside:avoid; }
  .grid.markets-grid { grid-template-columns:minmax(0,3fr) minmax(0,2fr); }
  .grid.markets-grid > .table-col { grid-column:1 / -1; border-left:0; padding:18px 0 0; margin-top:16px; border-top:1px solid var(--rule); }
}
@media (max-width:760px) {
  body { font-size:16px; }
  .utility .hide-sm { display:none; }
  .masthead h1 { font-stretch:condensed; font-size:clamp(2rem,10.4vw,3.4rem); }
  .motto { font-size:.95rem; gap:12px; }
  .motto::before, .motto::after { width:28px; }
  nav.sections { flex-wrap:nowrap; justify-content:flex-start; overflow-x:auto; gap:20px; scrollbar-width:none; padding-left:2px;
                 -webkit-mask-image:linear-gradient(90deg,#000 82%,transparent); mask-image:linear-gradient(90deg,#000 82%,transparent); }
  .markets { display:flex; overflow-x:auto; scroll-snap-type:x mandatory; scrollbar-width:none;
             -webkit-mask-image:linear-gradient(90deg,#000 88%,transparent); mask-image:linear-gradient(90deg,#000 88%,transparent); }
  .mk { flex:0 0 auto; min-width:156px; scroll-snap-align:start; border-top:0; border-left:1px solid var(--rule); }
  .mk:first-child { border-left:0; }
  .mk .top, .mk .fig { gap:14px; }
  .front, .grid, .grid.markets-grid, .related .grid, .explain { grid-template-columns:minmax(0,1fr); }
  .front > * + *, .grid > * + * { border-left:0; }
  .lead, .rail, .grid > * { padding:0; }
  .lead .excerpt { display:none; }
  .front > .whats { order:1; }
  .front > .rail { order:2; }
  .rail { margin-top:24px; padding-top:18px; border-top:1px solid var(--rule); }
  .grid > * + * { border-top:1px solid var(--rule); padding-top:14px; }
  .grid.markets-grid > .table-col { padding-top:14px; margin-top:0; }
  .explain section + section { border-left:0; padding-left:0; border-top:1px solid var(--rule); }
  .explain section:first-child { padding-right:0; }
  .topbar nav.sections { display:none; }
  footer .wrap { grid-template-columns:1fr; gap:10px; }
}
@media (prefers-reduced-motion:reduce) {
  @view-transition { navigation:none; }
  .hl, .arrow, nav.sections a::after { transition:none; }
}
"""

# First-visit gate for the edition opening; runs in <head> before paint. Any failure leaves the final state.
OPEN_GATE = """<script>(function(){try{if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
if(sessionStorage.getItem('opened'))return;sessionStorage.setItem('opened','1');var r=document.documentElement;
r.classList.add('edition-open');setTimeout(function(){r.classList.remove('edition-open');},2600);}catch(e){}})();</script>"""

# Splits the lead headline into its rendered lines once the display face has loaded, so each line
# can be pulled separately, then restores the plain text. Without the face or JS the headline just shows.
LINE_SPLIT = """<script>(function(){var r=document.documentElement;if(!r.classList.contains('edition-open'))return;
var h=document.querySelector('.lead h2 .hl');if(!h)return;var orig=h.textContent;
var esc=function(s){return s.replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});};
var go=function(){if(!r.classList.contains('edition-open'))return;var words=orig.trim().split(/\\s+/);
h.innerHTML=words.map(function(w){return'<span class="w">'+esc(w)+'</span>';}).join(' ');
var lines=[],top=null;h.querySelectorAll('.w').forEach(function(s){if(s.offsetTop!==top){top=s.offsetTop;lines.push([]);}lines[lines.length-1].push(s.textContent);});
h.innerHTML=lines.map(function(l,i){return'<span class="ln" style="--i:'+i+'">'+esc(l.join(' '))+'</span>';}).join('');
r.classList.add('lines-ready');setTimeout(function(){h.textContent=orig;r.classList.remove('lines-ready');},1200+lines.length*120);};
var f=document.fonts,wait=new Promise(function(res){setTimeout(res,300);});
Promise.race([f&&f.load?f.load('condensed 700 48px "Noto Serif Display"'):Promise.resolve(),wait]).then(go,go);})();</script>"""

SITE_JS = """(function(){
var p=document.querySelector('.progress'),a=document.querySelector('article.piece');
if(p&&a){var queued=false,update=function(){queued=false;var r=a.getBoundingClientRect(),h=r.height-innerHeight;
p.style.setProperty('--p',Math.min(1,Math.max(0,h>0?-r.top/h:1)).toFixed(4));};
addEventListener('scroll',function(){if(!queued){queued=true;requestAnimationFrame(update);}},{passive:true});
addEventListener('resize',update);update();}
})();"""

# Which FRED series illustrates a Markets & Economy article, by keywords in its headline and topics.
CHART_KEYWORDS = [
    (("inflation", "cpi", "consumer price"), "CPIAUCNS"),
    (("unemployment", "jobless", "payroll", "labor market"), "UNRATE"),
    (("treasury", "bond", "yield", "imf", "debt"), "DGS10"),
    (("oil", "brent", "crude", "gasoline"), "DCOILBRENTEU"),
    (("nasdaq", "chip", "ai stocks", "tech stocks"), "NASDAQCOM"),
    (("vix", "volatility"), "VIXCLS"),
    (("dollar", "currency"), "DTWEXBGS"),
    (("fed ", "rate hike", "interest rate", "federal reserve", "wholesale", "producer price"), "DFF"),
    (("stocks", "s&p", "wall street", "shares"), "SP500"),
]


def _when(iso: str | None) -> str:
    return datetime.fromisoformat(iso).strftime("%b %d, %Y %H:%M UTC") if iso else ""


def _vt(a: dict) -> str:
    """Shared view-transition name for an article's headline on every page it appears."""
    return "h-" + re.sub(r"[^a-z0-9-]", "", a["id"].lower())


def _hl(text: str) -> str:
    return f'<span class="hl">{escape(text)}</span>'


def _read_time(a: dict) -> int:
    return max(1, round(sum(len(p.split()) for p in a["body"]) / 230))


def _link(a: dict, root: str) -> str:
    return f"{root}articles/{a['id']}.html"


def _next_edition(iso: str) -> str:
    t = datetime.fromisoformat(iso)
    nxt = t.replace(hour=12, minute=0) if t.hour < 12 else (t + timedelta(days=1)).replace(hour=0, minute=0)
    return nxt.strftime("%H:%M UTC")


def _short_date(d: str) -> str:
    return datetime.fromisoformat(d).strftime("%b %d").replace(" 0", " ")


# ---------------------------------------------------------------- figures

def _value(ind: dict) -> str:
    v, kind = ind["value"], ind.get("kind", "rate")
    if kind == "rate":
        return f"{v:.2f}%"
    if kind == "usd":
        return f"${v:,.2f}"
    return f"{v:,.2f}"


def _signed(x: float, suffix: str = "") -> tuple[str, str]:
    cls = "up" if x > 0 else "down" if x < 0 else "flat"
    sign = "+" if x > 0 else "−" if x < 0 else "±"
    return f"{sign}{abs(x):,.2f}{suffix}", cls


def _change(ind: dict) -> tuple[str, str]:
    if ind.get("kind") in ("index", "usd"):
        return _signed(ind.get("change_pct", 0.0), "%")
    return _signed(ind["change"])


def _window_change(ind: dict) -> tuple[str, str]:
    h = ind.get("history") or []
    if len(h) < 2:
        return "", "flat"
    if ind.get("kind") in ("index", "usd"):
        return _signed((h[-1] / h[0] - 1) * 100 if h[0] else 0.0, "%")
    return _signed(h[-1] - h[0])


def _spark(values: list[float], delay_ms: int = 300) -> str:
    """A stretchable sparkline: the line is SVG, the end point an HTML dot so it stays round."""
    if not values or len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    n = len(values) - 1
    pts = [(i / n * 100, 92 - (v - lo) / span * 84) for i, v in enumerate(values)]
    d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
    ex, ey = pts[-1]
    return (f'<span class="sp" aria-hidden="true"><svg viewBox="0 0 100 100" preserveAspectRatio="none">'
            f'<path class="spark" pathLength="1" style="--d:{delay_ms}ms" d="{d}"/></svg>'
            f'<i class="dot" style="left:{ex:.2f}%;top:{ey:.2f}%;--d:{delay_ms}ms"></i></span>')


def _markets(indicators: list[dict]) -> str:
    if not indicators:
        return ""
    cells = []
    for i, ind in enumerate(indicators):
        chg, cls = _change(ind)
        cells.append(f'<div class="mk"><div class="top"><span class="name">{escape(ind["label"])}</span>'
                     f'<span class="asof">{_short_date(ind["as_of"])}</span></div>'
                     f'<div class="fig"><span class="val">{_value(ind)}</span><span class="chg {cls}">{chg}</span></div>'
                     f'{_spark(ind.get("history", []), 260 + i * 60)}</div>')
    return f'<section class="markets" aria-label="Market data">{"".join(cells)}</section>'


def _markets_table(indicators: list[dict]) -> str:
    rows = []
    for ind in indicators:
        chg, cls = _change(ind)
        wchg, wcls = _window_change(ind)
        rows.append(f'<tr><td>{escape(ind["label"])}</td><td>{_value(ind)}</td><td class="{cls}">{chg}</td>'
                    f'<td class="{wcls}">{wchg}</td><td class="trend">{_spark(ind.get("history", []))}</td></tr>')
    return (f'<table class="mtable"><caption><h3 class="col-head">Markets at a Glance</h3></caption>'
            f'<thead><tr><th scope="col">Series</th><th scope="col">Last</th><th scope="col">Chg</th>'
            f'<th scope="col">Period</th><th scope="col"><span style="position:absolute;left:-9999px">Trend</span></th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
            f'<p class="meta table-note">Chg is the latest move; Period covers about three months of daily data, or two years for '
            f'monthly series. Source: FRED, Federal Reserve Bank of St. Louis.</p>')


def _nice_step(raw: float) -> float:
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw:
            return m * mag
    return 10 * mag


def _chart(ind: dict) -> str:
    """An authored line chart of one FRED series, laid out in HTML around a stretchable SVG line."""
    h = ind.get("history") or []
    if len(h) < 6:
        return ""
    lo, hi = min(h), max(h)
    step = _nice_step(((hi - lo) or abs(hi) * .1 or 1) / 3)
    y0, y1 = math.floor(lo / step) * step, math.ceil(hi / step) * step
    if y1 == y0:
        y1 = y0 + step
    ticks = [y0 + i * step for i in range(int(round((y1 - y0) / step)) + 1)]
    yp = lambda v: 100 - (v - y0) / (y1 - y0) * 100
    n = len(h) - 1
    d = "M" + " L".join(f"{i / n * 100:.2f} {yp(v):.2f}" for i, v in enumerate(h))
    grid = "".join(f'<path class="grid-line" d="M0 {yp(t):.2f} H100"/>' for t in ticks)
    decimals = 0 if step >= 1 else 1 if step >= .1 else 2
    labels = "".join(f'<span class="yt" style="top:{yp(t):.2f}%">{t:,.{decimals}f}</span>' for t in ticks)
    ey = yp(h[-1])
    unit = {"rate": "per cent", "usd": "US dollars per barrel", "index": "index level", "level": "index level"}[ind.get("kind", "rate")]
    since = ind.get("since")
    start = datetime.fromisoformat(since).strftime("%b %Y") if since else ""
    return (f'<figure class="chart"><figcaption><b>{escape(ind["label"])}</b>{unit}, latest {_value(ind)}</figcaption>'
            f'<div class="plot"><svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">{grid}'
            f'<path class="line" d="{d}"/></svg>{labels}'
            f'<i class="dot" style="left:100%;top:{ey:.2f}%"></i><span class="endlab" style="left:100%;top:{ey:.2f}%">{_value(ind)}</span></div>'
            f'<div class="xaxis"><span>{start}</span><span>{_short_date(ind["as_of"])}, {ind["as_of"][:4]}</span></div>'
            f'<p class="meta">Source: FRED, Federal Reserve Bank of St. Louis. Latest observation {escape(ind["as_of"])}.</p></figure>')


def _chart_for(a: dict, indicators: list[dict]) -> str:
    if a["section"] != "markets":
        return ""
    by_id = {i.get("id"): i for i in indicators}
    text = " ".join([a["headline"], a["dek"], " ".join(a["topics"])]).lower()
    for words, sid in CHART_KEYWORDS:
        if any(w in text for w in words) and sid in by_id:
            return _chart(by_id[sid])
    return ""


# ---------------------------------------------------------------- page parts

def _page(title: str, body: str, root: str, head_extra: str = "") -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#fcf0e4">
<title>{escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="{root}style.css">
{head_extra}
</head><body>{body}
<footer><div class="wrap"><a class="logo" href="{root}index.html">The Daily Spin</a>
<p>Satire written by AI from real reporting, in a new edition every 12 hours. The facts are meant to be accurate; the tone is not meant
to be neutral. Every article names and links its original sources. Market data from FRED, Federal Reserve Bank of St. Louis.</p></div></footer>
<script src="{root}site.js" defer></script>
</body></html>"""


def _nav(root: str, front: bool, current: str = "") -> str:
    href = "#" if front else f"{root}index.html#"
    current_attr = ' aria-current="true"'
    links = "".join(f'<a href="{href}{k}"{current_attr if k == current else ""}>{escape(v["title"])}</a>'
                    for k, v in SECTIONS.items())
    return f'<nav class="sections" aria-label="Sections">{links}</nav>'


def _wire_line(a: dict) -> str:
    wire = a.get("wire_headline")
    if not wire:
        return ""
    return f'<p class="wireline">The wire said: <s>{escape(wire)}</s> &middot; {escape(a.get("wire_source", ""))}</p>'


def _byline(a: dict, right: str) -> str:
    return (f'<div class="byline"><span>By <b>The Daily Spin Desk</b> &middot; <span class="sec">{escape(a["section_title"])}</span></span>'
            f'<span>{right}</span></div>')


def _story(a: dict, root: str, top: bool = False, section_label: bool = False, paras: int = 1) -> str:
    sec = f'<span class="sec">{escape(a["section_title"])}</span> &middot; ' if section_label else ""
    dek_cls = ' class="standfirst"' if top else ""
    excerpt = "".join(f'<p>{escape(p)}</p>' for p in a["body"][:paras]) if top else ""
    return (f'<a class="story{" top" if top else ""}" href="{_link(a, root)}">'
            f'<h3 style="view-transition-name:{_vt(a)}">{_hl(a["headline"])}</h3>'
            f'<p{dek_cls}>{escape(a["dek"])}</p>{excerpt}'
            f'<div class="meta">{sec}{_read_time(a)} min read</div></a>')


def _wire(items: list[dict], limit: int = 6) -> str:
    if not items:
        return ""
    links = '<span class="sep" aria-hidden="true"></span>'.join(
        f'<a href="{escape(w["url"])}" target="_blank" rel="noopener">{escape(w["title"])}</a> <span class="src">{escape(w["source"])}</span>'
        for w in items[:limit])
    return f'<div class="wire"><h3>Elsewhere on the wire</h3>{links}</div>'


def _ears(data: dict) -> tuple[str, str]:
    gen = data["generated_at"]
    t = datetime.fromisoformat(gen)
    left = f'<div class="ear left"><b>Edition of {t:%H:%M} UTC</b>Next edition {_next_edition(gen)}<br>Twice daily</div>'
    arts = data["articles"]
    outlets = len({src["name"] for a in arts for src in a["sources"]})
    right = (f'<div class="ear right"><b>In this edition</b>{len(arts)} stories from {outlets} outlets<br>'
             f'4 sections, rewritten with a straight face</div>')
    return left, right


# ---------------------------------------------------------------- pages

def render_front(data: dict) -> str:
    arts = data["articles"]
    b = data.get("briefing")
    lead = arts[b["lead_index"]] if b else arts[0]
    gen = data["generated_at"]
    model = f"Written by {data['model']}" if data["model"] else "Placeholder text (AI writing off)"

    excerpt = "".join(f"<p>{escape(p)}</p>" for p in lead["body"][:2])
    lead_html = f"""<a class="lead" href="{_link(lead, '')}">
<h2 style="view-transition-name:{_vt(lead)}">{_hl(lead["headline"])}</h2>
{LINE_SPLIT}
<p class="standfirst">{escape(lead["dek"])}</p>
{_wire_line(lead)}
{_byline(lead, f"{_read_time(lead)} min read")}
<div class="excerpt">{excerpt}</div>
<span class="more">Continue reading {ARROW}</span>
</a>"""

    whats = '<section class="whats"></section>'
    if b:
        items = "".join(f"<li>{escape(t)}</li>" for t in b["five_things"])
        whats = f'<section class="whats" aria-label="5 Things in 60 Seconds"><h2 class="col-head">5 Things in 60 Seconds</h2><ol>{items}</ol></section>'

    # Right rail: the Number of the Day, then each other section's top story.
    seen, rail_stories = {lead["section"]}, []
    for a in sorted(arts, key=lambda a: a["rank"]):
        if a["section"] not in seen:
            seen.add(a["section"])
            rail_stories.append(a)
    number = ""
    if b:
        n = b["number_of_the_day"]
        number = (f'<div class="number"><h2 class="col-head">Number of the Day</h2><div class="big">{escape(n["figure"])}</div>'
                  f'<p>{escape(n["explanation"])}</p></div>')
    rail = (f'<aside class="rail" aria-label="Top stories">{number}<h2 class="col-head">Top Stories</h2>'
            f'{"".join(_story(a, "", section_label=True) for a in rail_stories)}</aside>')

    shown = {id(lead)} | {id(a) for a in rail_stories}
    sections = []
    for key, cfg in SECTIONS.items():
        sec = sorted((a for a in arts if a["section"] == key and id(a) not in shown), key=lambda a: a["rank"])
        if not sec:
            continue
        top, rest = sec[0], sec[1:]
        stack = f'<div>{"".join(_story(a, "") for a in rest)}</div>' if rest else ""
        has_table = key == "markets" and any(i.get("history") for i in data["indicators"])
        table = f'<div class="table-col">{_markets_table(data["indicators"])}</div>' if has_table else ""
        grid_cls = "grid markets-grid" if table else "grid"
        count = sum(1 for a in arts if a["section"] == key)
        sections.append(f'<section class="section" id="{key}"><div class="section-head"><h2>{escape(cfg["title"])}</h2>'
                        f'<span class="meta">{count} stories this edition</span></div>'
                        f'<div class="{grid_cls}">{_story(top, "", top=True, paras=(3 if table else 2) if len(rest) >= 3 else 1)}{stack}{table}</div>'
                        f'{_wire(data["wire"].get(key, []))}</section>')

    t = datetime.fromisoformat(gen)
    ear_left, ear_right = _ears(data)
    body = f"""<div class="wrap">
<div class="utility"><span><b>{t:%A, %B} {t.day}, {t:%Y}</b></span>
<span><span class="narrow">Edition of {t:%H:%M} UTC &middot; next {_next_edition(gen)}</span><span class="hide-sm"><span class="narrow"> &middot; </span>{escape(model)}</span></span></div>
<header class="masthead">{ear_left}<h1><span class="the">The</span>Daily Spin</h1>{ear_right}</header>
<p class="motto">Real news. Unreal commentary.</p><div class="double"></div>
{_nav("", True)}
{_markets(data["indicators"])}
<main>
<div class="front">{whats}{lead_html}{rail}</div>
{"".join(sections)}
</main>
</div>"""
    return _page("The Daily Spin", body, "", OPEN_GATE)


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
    related = "".join(f"<div>{_story(r, root, section_label=True)}</div>" for r in _related(a, data["articles"]))
    body = f"""<header class="topbar"><div class="wrap"><a class="logo" href="{root}index.html">The Daily Spin</a>
{_nav(root, False, a["section"])}</div><div class="progress" aria-hidden="true"></div></header>
<div class="wrap">
<main>
<article class="piece">
<h1 style="view-transition-name:{_vt(a)}">{escape(a["headline"])}</h1>
<p class="standfirst">{escape(a["dek"])}</p>
{_wire_line(a)}
{_byline(a, f'{_when(data["generated_at"])} &middot; {_read_time(a)} min read')}
<div class="explain"><section><h2>Catch up</h2>{escape(a["catch_up"])}</section>
<section><h2>Why it matters</h2>{escape(a["why_it_matters"])}</section></div>
{_chart_for(a, data["indicators"])}
<div class="body">{paras}</div>
<p class="sources">Satire based on reporting by {sources}. Read the originals for the straight version.</p>
</article>
<section class="related" aria-label="Related coverage"><div class="section-head"><h2>Related coverage</h2></div>
<div class="grid">{related}</div>{_wire(data["wire"].get(a["section"], []), 8)}</section>
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
