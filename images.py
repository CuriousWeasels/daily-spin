"""Openly licensed illustrative photos from Openverse (Creative Commons and public domain),
plus a sanitizer for the Claude-drawn cartoon SVG.

Openverse's anonymous API allows ~20 requests a minute and ~200 a day, so searches are spaced
out; an edition needs about 20.
"""

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "https://api.openverse.org/v1/images/"
USER_AGENT = "DailySpinBot/0.3 (+https://curiousweasels.github.io/daily-spin/)"
LICENSES = "by,by-sa,cc0,pdm"     # reuse allowed with attribution; no NC/ND
CANDIDATES = 8
SPACING = 3.3                     # seconds between searches, under the burst limit
LICENSE_LABELS = {"by": "CC BY", "by-sa": "CC BY-SA", "cc0": "CC0", "pdm": "Public domain"}


def _get_json(url: str, attempts: int = 2) -> dict | None:
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=12) as resp:
                return json.load(resp)
        except Exception as e:
            if i == attempts - 1:
                print(f"  ! image search failed: {e}", file=sys.stderr)
            time.sleep(2)
    return None


def _display_url(c: dict) -> str:
    """A web-sized version of the file: Wikimedia serves resized thumbnails on request."""
    url, width = c["url"], c.get("width") or 0
    m = re.match(r"https://upload\.wikimedia\.org/wikipedia/commons/([0-9a-f])/([0-9a-f]{2})/(.+)$", url)
    if m and width > 1400:
        a, ab, name = m.groups()
        return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{ab}/{name}/1280px-{name}"
    return url


COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def _commons_license(short: str) -> tuple[str, str] | None:
    """Map a Commons license name to (openverse-style code, version); None if reuse isn't allowed."""
    s = short.strip()
    if re.search(r"\b(NC|ND)\b", s):
        return None
    m = re.match(r"CC BY(-SA)? ?([\d.]+)?", s)
    if m:
        return ("by-sa" if m.group(1) else "by"), (m.group(2) or "")
    if s.upper().startswith("CC0"):
        return "cc0", ""
    if s.lower().startswith("public domain"):
        return "pdm", ""
    return None


def search_commons(query: str) -> list[dict]:
    """Fallback straight to Wikimedia Commons, which hosts most openly licensed news-adjacent photos."""
    params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {query}",
              "gsrnamespace": 6, "gsrlimit": CANDIDATES * 2, "prop": "imageinfo", "iiprop": "url|size|extmetadata",
              "iiurlwidth": 1280, "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist"}
    data = _get_json(COMMONS_API + "?" + urllib.parse.urlencode(params), attempts=1)
    out = []
    for page in ((data or {}).get("query") or {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        lic = _commons_license(meta.get("LicenseShortName", {}).get("value", ""))
        w, h = info.get("thumbwidth") or 0, info.get("thumbheight") or 0
        if not lic or not info.get("thumburl") or w < h * 1.2:      # landscape only
            continue
        artist_html = meta.get("Artist", {}).get("value", "")
        link = re.search(r'href="([^"]+)"', artist_html)
        title = re.sub(r"^File:|\.[a-zA-Z]{3,4}$", "", page["title"]).replace("_", " ")
        out.append({
            "title": title, "tags": [], "creator": html.unescape(re.sub(r"<[^>]+>", "", artist_html)).strip()[:80],
            "creator_url": html.unescape(("https:" + link.group(1)) if link and link.group(1).startswith("//") else (link.group(1) if link else "")),
            "license": lic[0], "license_version": lic[1], "license_url": meta.get("LicenseUrl", {}).get("value", ""),
            "landing_url": info.get("descriptionurl") or "", "source": "wikimedia",
            "url": info["thumburl"].split("?")[0], "width": w, "height": h,
        })
    return out[:CANDIDATES]


def search(query: str) -> list[dict]:
    """Openverse first (wider range of sources), Wikimedia Commons if it is slow or finds nothing."""
    results = search_openverse(query)
    return results or search_commons(query)


def search_openverse(query: str) -> list[dict]:
    params = {"q": query, "license": LICENSES, "aspect_ratio": "wide", "size": "large",
              "page_size": CANDIDATES, "mature": "false"}
    data = _get_json(API + "?" + urllib.parse.urlencode(params), attempts=1)
    out = []
    for r in (data or {}).get("results", []):
        if not r.get("url") or not r.get("license"):
            continue
        out.append({
            "title": (r.get("title") or "Untitled").strip(),
            "tags": [t["name"] for t in (r.get("tags") or [])][:6],
            "creator": (r.get("creator") or "").strip(),
            "creator_url": r.get("creator_url") or "",
            "license": r["license"],
            "license_version": r.get("license_version") or "",
            "license_url": r.get("license_url") or "",
            "landing_url": r.get("foreign_landing_url") or "",
            "source": r.get("source") or "",
            "url": r["url"],
            "width": r.get("width") or 0,
            "height": r.get("height") or 0,
        })
    return out


def search_all(queries: list[str]) -> list[list[dict]]:
    results = []
    for i, q in enumerate(queries):
        if i:
            time.sleep(SPACING)
        results.append(search(q) if q else [])
    return results


def to_image(c: dict) -> dict:
    """The fields a page needs to show the photo and its required credit."""
    label = LICENSE_LABELS.get(c["license"], c["license"].upper())
    if c["license"] in ("by", "by-sa") and c["license_version"]:
        label += f" {c['license_version']}"
    w, h = c["width"], c["height"]
    if w > 1280:
        w, h = 1280, round(h * 1280 / w)
    return {"src": _display_url(c), "width": w, "height": h, "title": c["title"], "creator": c["creator"],
            "creator_url": c["creator_url"], "license": label, "license_url": c["license_url"],
            "landing_url": c["landing_url"], "source": "Wikimedia Commons" if c["source"] == "wikimedia" else c["source"].title()}


# ---------------------------------------------------------------- cartoon SVG

_DROP_TAGS = {"script", "foreignobject", "image", "a", "style", "iframe", "object", "embed", "audio", "video", "animate",
              "set", "animatemotion", "animatetransform"}


def _local(tag: str) -> str:
    return tag.split("}")[-1].lower()


def sanitize_svg(svg: str, max_bytes: int = 250_000) -> str | None:
    """Keep only static vector drawing: no scripts, links, external references or embedded content."""
    if len(svg.encode()) > max_bytes or re.search(r"<!(DOCTYPE|ENTITY)", svg, re.I):
        return None
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return None
    if _local(root.tag) != "svg":
        return None
    for parent in list(root.iter()):
        for child in list(parent):
            if _local(child.tag) in _DROP_TAGS:
                parent.remove(child)
    for el in root.iter():
        for attr in list(el.attrib):
            name, val = _local(attr), el.attrib[attr]
            if name.startswith("on") or (name == "href" and not val.startswith("#")) or "url(" in val and "url(#" not in val:
                del el.attrib[attr]
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    if not root.tag.startswith("{"):   # served as a file, an SVG without its namespace will not render
        root.set("xmlns", "http://www.w3.org/2000/svg")
    return ET.tostring(root, encoding="unicode")
