---
name: The Daily Spin
description: A premium financial daily in the WSJ/FT tradition, played perfectly straight so the satire lands.
colors:
  paper: "#ffffff"
  paper-2: "#f5f4f1"
  ink: "#1a1a1a"
  ink-2: "#3a3a3a"
  muted: "#5f5f5f"
  rule: "#d9d9d6"
  rule-strong: "#1a1a1a"
  claret: "#8c1f3c"
  data: "#1f4e86"
  up: "#0b6b3c"
  down: "#a8231c"
typography:
  masthead:
    fontFamily: "'Noto Serif Display', Georgia, serif"
    fontSize: "clamp(2.7rem, 6.6vw, 5.4rem)"
    fontWeight: 900
    lineHeight: 0.95
    letterSpacing: "-0.012em"
    fontVariation: "'wdth' 87.5"
  display:
    fontFamily: "'Noto Serif Display', Georgia, serif"
    fontSize: "clamp(2.1rem, 3.9vw, 3.5rem)"
    fontWeight: 700
    lineHeight: 1.03
    letterSpacing: "-0.008em"
    fontVariation: "'wdth' 75"
  headline:
    fontFamily: "'Noto Serif Display', Georgia, serif"
    fontSize: "1.9rem"
    fontWeight: 800
    lineHeight: 1.1
    fontVariation: "'wdth' 87.5"
  title:
    fontFamily: "'Source Serif 4', Georgia, serif"
    fontSize: "1.14rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.005em"
  standfirst:
    fontFamily: "'Source Serif 4', Georgia, serif"
    fontSize: "1.22rem"
    fontWeight: 400
    lineHeight: 1.45
  body:
    fontFamily: "'Source Serif 4', Georgia, serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.55
  body-article:
    fontFamily: "'Source Serif 4', Georgia, serif"
    fontSize: "1.16rem"
    fontWeight: 400
    lineHeight: 1.72
  label:
    fontFamily: "'Libre Franklin', 'Franklin Gothic Medium', 'Arial Narrow', Arial, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 800
    letterSpacing: "0.09em"
  meta:
    fontFamily: "'Libre Franklin', 'Franklin Gothic Medium', 'Arial Narrow', Arial, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 400
    fontFeature: "'tnum' 1"
  figure:
    fontFamily: "'Libre Franklin', 'Franklin Gothic Medium', 'Arial Narrow', Arial, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 700
    letterSpacing: "-0.01em"
    fontFeature: "'tnum' 1"
rounded:
  none: "0"
  dot: "50%"
spacing:
  page-gutter: "20px"
  item: "12px"
  column: "22px"
  column-wide: "30px"
  block: "30px"
components:
  col-head:
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    padding: "8px 0 0"
  section-tag:
    textColor: "{colors.claret}"
    typography: "{typography.meta}"
  nav-link:
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    padding: "3px 0"
  masthead-ear:
    textColor: "{colors.muted}"
    typography: "{typography.meta}"
    padding: "8px 0"
    width: "220px"
  market-cell:
    backgroundColor: "{colors.paper-2}"
    textColor: "{colors.ink}"
    typography: "{typography.figure}"
    padding: "9px 14px 8px"
  story:
    textColor: "{colors.ink}"
    typography: "{typography.title}"
    padding: "0 0 14px"
  explainer-label:
    textColor: "{colors.claret}"
    typography: "{typography.label}"
  more-link:
    textColor: "{colors.claret}"
    typography: "{typography.meta}"
  progress-rule:
    backgroundColor: "{colors.claret}"
    height: "2px"
  chart-line:
    textColor: "{colors.data}"
    height: "200px"
---

# Design System: The Daily Spin

## Overview

**Creative North Star: "The Paper of Record, Played Straight"**

The Daily Spin dresses as a premium financial daily in the Wall Street Journal and Financial Times tradition and never winks. Crisp white newsprint, near-black ink, hairline column rules, a heavy-light double rule under a centred uppercase masthead, and a band of real FRED figures with drawn sparklines give it the gravity of a paper of record; the deadpan satire lives entirely in the words. The craft bar is the real papers themselves, not a generic news portal.

Density is broadsheet density: a three-column front page (briefing, lead, rail), multi-column section grids, a markets table, and a wire digest, all separated by rules rather than whitespace and boxes. Surfaces are flat paper. Hierarchy comes from type weight, width, and rule weight. Article pages narrow to a single 740px reading column with a drop cap, a two-part explainer panel, and, for markets stories, a FRED line chart. Colour is scarce: one claret accent, one oxford blue reserved for data.

Motion is ceremonial and brief: the edition opens once per session (the masthead double rule draws out, the lead headline unmasks line by line, sparklines plot), headlines morph into article titles across page navigations, and hover states draw underlines. All of it yields to `prefers-reduced-motion`.

**Key Characteristics:**
- White paper ground (the owner's choice) with near-black ink.
- Three type voices: condensed high-contrast display serif, text serif, Franklin gothic for labels and figures.
- Rule weight as hierarchy: 3px ink heads, 1px ink closes, 1px warm-gray hairline separates.
- One claret accent; oxford blue only for plotted data; green and red only for change figures.
- Flat, square-cornered, shadowless; the only round shapes are data dots.
- Tabular lining figures wherever numbers appear.

## Colors

A warm, near-monochrome newsprint palette with one claret accent and one data blue.

### Primary
- **Masthead Claret**: the single accent. Section tags in meta lines and bylines, explainer labels ("Catch up", "Why it matters"), the "Continue reading" link, the Number of the Day figure, the square bullets of the briefing list, the nav hover/current underline, the article reading-progress rule, the strike line through the original wire headline, and the focus outline.

### Secondary
- **Oxford Data Blue**: plotted data only. Sparkline strokes, chart lines, end dots, and the chart end label. Never used for links or text decoration.

### Tertiary
- **Ledger Green** (up) and **Ledger Red** (down): change figures in the markets band and markets table, nothing else. Unchanged values use Muted Umber.

### Neutral
- **Newsprint White**: the page ground and the sticky article top bar.
- **Market Stock Gray**: the one tinted surface, the markets band behind the market figures.
- **Press Ink**: headlines, body text, and every strong rule (Rule Strong carries the same value in its structural role).
- **Soft Ink**: standfirsts, story deks, explainer text, secondary copy.
- **Muted Umber**: metadata, timestamps, ears, axis labels, table headers, source lines.
- **Hairline Tan**: 1px column rules, item separators, chart gridlines, link underlines at rest, the motto flourishes.

### Named Rules
**The One Claret Rule.** Claret is the only accent and marks the paper's own voice: section tags, explainer labels, the number of the day, interaction underlines. It never fills a surface.

**The Blue Means Data Rule.** Oxford blue appears only where a real series is plotted. If it is not a FRED line or its end value, it is not blue.

**The White Ground Rule.** The page ground is white, the owner's choice after trying the FT-style pink. Never tint it pink, cream or beige; the markets band is the only tinted surface.

## Typography

**Display Font:** Noto Serif Display (with Georgia, serif), variable width and weight
**Body Font:** Source Serif 4 (with Georgia, serif), optical sizing on
**Label/Mono Font:** Libre Franklin (with Franklin Gothic Medium, Arial Narrow, Arial)

**Character:** A sharp, high-contrast transitional display serif squeezed to condensed and semi-condensed widths gives headlines the urgency of a financial front page; a sturdy text serif carries long reading; a Franklin gothic does every job a gothic does on a real paper: labels, figures, bylines, tables.

**Delivery:** all three families are self-hosted in `docs/fonts/` (latin and latin-ext subsets only, `font-display: swap`, Georgia and Arial fallbacks), fetched from Google Fonts by `get_fonts.py` and licensed under the SIL Open Font License 1.1 (license texts sit beside the files). Pages link `fonts/fonts.css` and preload the upright Noto Serif Display and Source Serif 4 latin files. No page requests a third-party font host; to add a weight or width, extend `CSS_URL` in `get_fonts.py` and rerun it.

### Hierarchy
- **Masthead** (900, semi-condensed, uppercase, clamp 2.7rem to 5.4rem, line-height 0.95): the nameplate only, with an italic 500 "The" set small and raised. Condensed width under 760px. The same face at 1.3 to 1.45rem names the paper in the article top bar and footer.
- **Display** (700, condensed, clamp 2.1rem to 3.5rem, line-height 1.03, balanced): the front-page lead. Article titles use the same voice at clamp 2.3rem to 3.7rem; section top stories at clamp 1.6rem to 2.1rem.
- **Headline** (800, semi-condensed, 1.9rem): section heads ("Geopolitics", "Related coverage"). The Number of the Day figure uses 800 semi-condensed at clamp 2.6rem to 3.5rem in claret.
- **Title** (Source Serif 700, 1.14rem, line-height 1.25, balanced): ordinary story units in the rail and section stacks.
- **Standfirst** (Source Serif 400, 1.22rem front, 1.32rem article, 1.06rem section top): the one-sentence dek, in Soft Ink.
- **Body** (Source Serif 400, 17px base, 16px under 760px, line-height 1.55). Article body runs 1.16rem at line-height 1.72, capped at 68ch, opening with a four-line display drop cap (800, 4.3rem).
- **Label** (Franklin 800, 0.75 to 0.78rem, letter-spacing 0.09em, uppercase): column heads, explainer labels, the wire digest head. Nav links are the lighter variant (600, 0.8rem, 0.06em).
- **Meta** (Franklin 400, 0.72 to 0.85rem, tabular): bylines, read times, ears, utility line, axis ticks, sources.
- **Figure** (Franklin 700, 1.15rem, tabular): market values; changes at 600, 0.8rem.

### Named Rules
**The Three Voices Rule.** Display serif for headlines and the nameplate, text serif for anything read as prose, Franklin gothic for anything read as information. A label is never set in serif; a paragraph is never set in gothic.

**The Tabular Figures Rule.** Every number in Franklin (markets, tables, ears, timestamps, axes) uses tabular numerals so columns of figures align.

## Layout

A centred 1260px page with 20px side gutters. The front page is a three-column broadsheet (250px briefing, fluid lead, 290px rail); the lead pads 30px from its rules, the briefing and rail 22px. Sections use a 3:2 grid with 24px column padding, or a 2 : 1.3 : 1.7 grid when the markets table joins the Markets section. The lead and section top stories run their excerpts in two newspaper columns (260px minimum, 28px gap, hairline column rule). Articles sit in a 740px column; related coverage spreads across four columns.

Spacing is set per component rather than drawn from a strict scale; recurring steps are 8px (rule-to-label), 12 to 14px (between list and story items), 18 to 22px (between blocks), and 26 to 30px (between major regions).

Responsive: at 1060px the masthead ears drop, the briefing moves below the lead and rail as a full-width two-column list, and the markets table moves under the Markets stories. At 760px everything stacks to one column, column rules turn into top rules, the briefing comes first after the lead, the lead excerpt hides, the section nav and markets band become horizontal scrollers (the band with scroll snap, both with a fade mask at the right edge), and the article top bar drops its nav.

**The Hairline Column Rule.** Columns are divided by 1px Hairline Tan rules, never by gutters alone or by boxes. When columns stack, the vertical rule becomes a horizontal one.

**The Rule Weight Rule.** A 3px Press Ink rule heads a column or section; a 1px Press Ink rule closes a band (nav, markets band, table header, top bar, footer); a 1px Hairline Tan rule separates items within a column. The masthead's 3px-over-1px double rule is the one heavy-light pair.

**The Flush to the Rule Exception.** Following newspaper convention, text sits flush against its rules: labels start 8px under the heading rule with no horizontal inset, outer columns carry no outer padding, and ears sit directly between their two ink rules. This is deliberate, not missing padding.

## Elevation & Depth

Flat newsprint. There are no shadows anywhere in the system. Depth is conveyed only by the single tinted surface (Market Stock Gray behind the markets band) and by rule weight. The sticky article top bar separates from the page with a 1px ink rule and an opaque paper background, not a shadow. Chart end dots get a 2px paper-coloured ring so they sit cleanly on the line.

**The Flat Newsprint Rule.** Nothing lifts off the page. If an element needs emphasis, give it a heavier rule or a heavier weight, never a shadow.

## Shapes

Square corners throughout: rules, bands, panels, table cells, the briefing's 7px square claret bullets, and the 4px square wire-digest separators. The only round shapes are data points: the 5px sparkline end dots and the 9px chart end dot. The recurring geometry is the horizontal rule: masthead double rule, motto flourishes (1px Hairline Tan lines either side of the italic motto), column-head rules, and the strike-through on the original wire headline.

## Components

### Navigation
- **Section nav:** centred row of Franklin 600 uppercase labels (0.8rem, 0.06em tracking, 30px gaps) between the double rule and a 1px ink rule. Hover, focus, and current page draw a 2px claret underline from the left (280ms). Under 760px it becomes a left-aligned horizontal scroller with a right-edge fade.
- **Article top bar:** sticky, opaque paper, 1px ink bottom rule, nameplate left and a compact nav right (hidden under 760px). A 2px claret progress rule along its bottom edge scales from the left with reading position.

### Masthead
Utility line in Muted Umber meta (edition time, model credit), then a three-part grid: left ear, centred uppercase nameplate, right ear. Each ear is a 220px block of meta between two 1px ink rules with a bold Press Ink first line (left: "Edition of HH:MM UTC" and the next edition; right: "In this edition", the story and outlet count). Below: the italic display motto flanked by hairline flourishes, then the 3px-over-1px double rule. Ears drop at 1060px, and their edition time moves into the utility line.

### Markets Band
Ten cells in a five-by-two grid on Market Stock Gray, each separated by a hairline rule, closed by a 1px ink rule. Each cell has an uppercase Franklin name and muted as-of date on top, the figure with its green or red change below, then a 22px sparkline in oxford blue with an end dot.

### Markets Table
A full-width Franklin table under a "Markets at a Glance" column head: uppercase muted 0.7rem headers right-aligned over a 1px ink rule, hairline row rules, bold first column, tabular figures, and a 64px trend column holding a 16px sparkline.

### Story Units
- **Story:** headline (Title), dek in Soft Ink, meta line with optional claret section tag and read time; separated by hairline rules. The headline carries a 1px underline that draws left to right on hover and focus (360ms).
- **Section top story:** display headline, larger standfirst, and two or three excerpt paragraphs set in two columns.
- **Lead:** display headline, standfirst, the "The wire said:" line with the original headline struck through in claret, a byline between hairlines, a two-column excerpt, and a claret "Continue reading" link whose arrow nudges 4px right on hover.

### Briefing Column ("5 Things in 60 Seconds")
Column head, then a list with 7px square claret bullets and hairline separators. Number of the Day sits atop the rail: column head, the claret display figure, a short explanation.

### Explainer Panel
On every article, two side-by-side sections ("Catch up", "Why it matters") under a 3px ink rule and over a hairline, divided by a hairline column rule. Labels are claret Franklin uppercase; text is Soft Ink serif. Stacks under 760px.

### FRED Line Chart
For markets articles: a figure between a 1px ink top rule and a hairline bottom rule. Caption has the series name in bold serif over a muted unit line. A 200px plot of hairline gridlines and a 2.25px oxford blue line, muted tabular y-ticks to the left, an end dot ringed in paper, and the latest value as a bold blue end label to the right of the dot. Start and end dates sit beneath; a FRED source line closes it.

### Wire Digest ("Elsewhere on the wire")
An inline run under a hairline: a Franklin label head, then links in Soft Ink with Hairline Tan underlines that darken to ink on hover, each followed by its muted source, separated by small square tan markers.

### Motion
- **Edition opening** (first visit per session, skipped under reduced motion): masthead double rule scales out from centre (760ms), lead headline lines unmask from below one after another (760ms each, 120ms stagger) once the display face has loaded, standfirst and wire line fade in, sparklines plot (1100ms, staggered) and their dots settle after. All on the house ease, `cubic-bezier(.16,1,.3,1)`.
- **Headline continuity:** cross-document view transitions; each story headline shares a transition name with its article title so it morphs (480ms) while the page cross-fades.
- **Reduced motion:** the opening never starts, view transitions are off, and hover underlines, nav underlines, and arrow nudges change state instantly.

## Do's and Don'ts

### Do:
- **Do** keep the white paper ground on every page; the owner chose it over the FT-style pink.
- **Do** separate columns and items with hairline rules and head them with the 3px ink rule.
- **Do** set every label, figure, byline, and table in Libre Franklin with tabular numerals.
- **Do** run headlines in the condensed display serif with balanced wrapping, and long text in Source Serif 4 capped at 68ch.
- **Do** reserve oxford blue for plotted FRED data and green/red for change figures.
- **Do** keep the original wire headline visible, struck through in claret, and the sources line on every article.
- **Do** gate every animation behind `prefers-reduced-motion` and let the page render in its final state without JavaScript.

### Don't:
- **Don't** add box-shadows, rounded corners, or card backgrounds; the only tinted surface is the markets band and the only circles are data dots.
- **Don't** use claret as a fill or for data, or blue for links.
- **Don't** set labels or section tags above headlines; section tags live in the meta line and byline below.
- **Don't** add photographs, illustrations, or invented logos; there are none to use.
- **Don't** pad text away from its rules to "fix" the flush newspaper setting.
