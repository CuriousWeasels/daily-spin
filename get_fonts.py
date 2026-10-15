"""Download the site's web fonts from Google Fonts into docs/fonts/ so pages serve them
from their own origin. Run once (or again to refresh):

    python get_fonts.py

Only the latin and latin-ext subsets and the exact weights/widths the design uses are kept.
All three families are licensed under the SIL Open Font License 1.1 (see docs/fonts/*.OFL.txt).
"""

import re
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "docs" / "fonts"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

# Noto Serif Display is served as static instances, so request only the ones render.py uses
# (width 75 = condensed, 87.5 = semi-condensed, 100 = normal).
CSS_URL = ("https://fonts.googleapis.com/css2"
           "?family=Noto+Serif+Display:ital,wdth,wght@0,75,700;0,75,900;0,87.5,800;0,87.5,900;0,100,800;1,100,400;1,100,500"
           "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400..600"
           "&family=Libre+Franklin:wght@400..800&display=swap")
SUBSETS = {"latin", "latin-ext"}
LICENSES = {
    "noto-serif-display": "https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifdisplay/OFL.txt",
    "source-serif-4": "https://raw.githubusercontent.com/google/fonts/main/ofl/sourceserif4/OFL.txt",
    "libre-franklin": "https://raw.githubusercontent.com/google/fonts/main/ofl/librefranklin/OFL.txt",
}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
        return r.read()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    css = get(CSS_URL).decode()
    blocks = re.findall(r"/\* ([\w-]+) \*/\s*(@font-face \{.*?\})", css, re.S)
    kept, saved, total = [], {}, 0
    for subset, block in blocks:
        if subset not in SUBSETS:
            continue
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
        # Variable fonts: several weights/widths share one file, so save each URL once.
        if url not in saved:
            family = re.search(r"font-family: '([^']+)'", block).group(1)
            style = re.search(r"font-style: (\w+)", block).group(1)
            saved[url] = f"{family.lower().replace(' ', '-')}-{style}-{subset}.woff2"
            data = get(url)
            (OUT / saved[url]).write_bytes(data)
            total += len(data)
        kept.append(f"/* {subset} */\n" + block.replace(url, saved[url]))
    header = ("/* Self-hosted from Google Fonts by get_fonts.py. Noto Serif Display, Source Serif 4 and\n"
              "   Libre Franklin are licensed under the SIL Open Font License 1.1; see the *.OFL.txt files here. */\n")
    (OUT / "fonts.css").write_text(header + "\n".join(kept) + "\n", encoding="utf-8")
    for slug, url in LICENSES.items():
        (OUT / f"{slug}.OFL.txt").write_bytes(get(url))
    print(f"{len(saved)} font files ({len(kept)} @font-face rules), {total / 1024:.0f} KB, written to {OUT}")


if __name__ == "__main__":
    main()
