"""Re-render every page from saved data, without calling Claude. Run after design changes:

    python rerender.py
"""

import json
from pathlib import Path

from render import render_article, write_site

DOCS = Path(__file__).parent / "docs"

# Older editions' article pages stay online (people may have links to them), so refresh them too.
for path in sorted((DOCS / "data" / "archive").glob("*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    for a in data.get("articles", []):
        (DOCS / "articles" / f"{a['id']}.html").write_text(render_article(a, data), encoding="utf-8")

write_site(json.loads((DOCS / "data" / "latest.json").read_text(encoding="utf-8")), DOCS)
print("Re-rendered all pages.")
