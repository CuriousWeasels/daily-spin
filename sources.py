"""Free news sources, grouped by section.

Every entry is a public RSS/Atom feed. Add or remove feeds freely: a feed that
fails to load is skipped with a warning, it never breaks the build.
"""

SECTIONS = {
    "geopolitics": {
        "title": "Geopolitics",
        "feeds": {
            "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
            "The Guardian": "https://www.theguardian.com/world/rss",
            "NPR World": "https://feeds.npr.org/1004/rss.xml",
            "DW": "https://rss.dw.com/rdf/rss-en-world",
        },
    },
    "ai": {
        "title": "AI",
        "feeds": {
            "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
            "MIT Technology Review": "https://www.technologyreview.com/feed/",
            "The Decoder": "https://the-decoder.com/feed/",
            "Ars Technica AI": "https://arstechnica.com/ai/feed/",
        },
    },
    "technology": {
        "title": "Technology",
        "feeds": {
            "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
            "The Verge": "https://www.theverge.com/rss/index.xml",
            "BBC Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
            "Hacker News": "https://hnrss.org/frontpage",
        },
    },
    "markets": {
        "title": "Markets & Economy",
        "feeds": {
            "CNBC Markets": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "CNBC Economy": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
            "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
            "Investing.com": "https://www.investing.com/rss/news_25.rss",
            "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
        },
    },
}

# Key market and economic numbers from FRED's public CSV endpoint (no API key needed).
# "yoy": True turns a price index into a year-over-year % change.
# "kind" sets how a figure is shown: "rate" (a % level; change in points, the default),
# "index" (a level; change in %), "usd" (a dollar price; change in %), "level" (change in points).
INDICATORS = [
    # SPY comes from live quote feeds, not FRED: regular close plus pre-market / after-hours (see fetch_spy).
    {"id": "SPY", "label": "SPY", "unit": "", "kind": "usd", "source": "quote", "unit_label": "US dollars per share"},
    {"id": "NASDAQCOM", "label": "Nasdaq", "unit": "", "kind": "index"},
    {"id": "VIXCLS", "label": "VIX", "unit": "", "kind": "level"},
    {"id": "DCOILBRENTEU", "label": "Brent crude", "unit": "", "kind": "usd", "unit_label": "US dollars per barrel"},
    {"id": "DTWEXBGS", "label": "Dollar index", "unit": "", "kind": "index"},
    {"id": "DGS2", "label": "2Y Treasury", "unit": "%"},
    {"id": "DGS10", "label": "10Y Treasury", "unit": "%"},
    {"id": "DFF", "label": "Fed Funds", "unit": "%"},
    # Not seasonally adjusted: the series behind the headline YoY number the BLS reports.
    {"id": "CPIAUCNS", "label": "CPI inflation (YoY)", "unit": "%", "yoy": True, "monthly": True},
    {"id": "UNRATE", "label": "Unemployment", "unit": "%", "monthly": True},
]
