"""
RSS fetcher — editorial AI news from reputable tech publications + Medium tag feeds.
Free, no API key required.

Sources:
  - The Verge (AI section)
  - MIT Technology Review (AI section)
  - Medium (tags: artificial-intelligence, llm, generative-ai, machine-learning)
"""

import xml.etree.ElementTree as ET
import requests
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone

FEEDS = [
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
    },
    # Medium tag feeds — surfaces top posts per tag (sorted by Medium's recommendation engine)
    {
        "name": "Medium · AI",
        "url": "https://medium.com/feed/tag/artificial-intelligence",
    },
    {
        "name": "Medium · LLM",
        "url": "https://medium.com/feed/tag/llm",
    },
    {
        "name": "Medium · Generative AI",
        "url": "https://medium.com/feed/tag/generative-ai",
    },
    {
        "name": "Medium · Machine Learning",
        "url": "https://medium.com/feed/tag/machine-learning",
    },
]

# Generic headers for most feeds
HEADERS = {"User-Agent": "DailyAIBrief/1.0 (personal dashboard)"}

# Medium blocks generic UAs — use a browser-like one for their feeds
HEADERS_MEDIUM = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

CUTOFF_DAYS = 3


def _parse_feed(feed: dict, cutoff: datetime) -> list[dict]:
    items = []
    try:
        headers = HEADERS_MEDIUM if "Medium" in feed["name"] else HEADERS
        resp = requests.get(feed["url"], headers=headers, timeout=12)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        # Handle both RSS (<item>) and Atom (<entry>) formats
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall(".//item") or root.findall(".//atom:entry", ns)

        for entry in entries:
            # Title
            title_el = entry.find("title") or entry.find("atom:title", ns)
            title = (title_el.text or "").strip() if title_el is not None else ""

            # URL
            link_el = entry.find("link") or entry.find("atom:link", ns)
            if link_el is not None:
                url = link_el.get("href") or (link_el.text or "").strip()
            else:
                url = ""

            # Description / summary
            desc_el = (
                entry.find("description")
                or entry.find("summary")
                or entry.find("atom:summary", ns)
                or entry.find("atom:content", ns)
            )
            snippet = ""
            if desc_el is not None and desc_el.text:
                # Strip any HTML tags naively
                import re
                snippet = re.sub(r"<[^>]+>", "", desc_el.text).strip()[:300]

            # Date filter
            pub_el = entry.find("pubDate") or entry.find("atom:published", ns) or entry.find("atom:updated", ns)
            if pub_el is not None and pub_el.text:
                try:
                    pub_date = parsedate_to_datetime(pub_el.text.strip())
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                    if pub_date < cutoff:
                        continue
                except Exception:
                    pass  # If we can't parse the date, include it anyway

            if title and url:
                items.append({
                    "title": title,
                    "url": url,
                    "source": feed["name"],
                    "snippet": snippet,
                })

    except Exception as e:
        print(f"[rss_news] {feed['name']} failed: {e}")

    return items


def fetch(max_per_feed: int = 8) -> list[dict]:
    """Return recent articles from editorial AI news sources."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=CUTOFF_DAYS)
    all_items = []

    for feed in FEEDS:
        items = _parse_feed(feed, cutoff)[:max_per_feed]
        all_items.extend(items)
        print(f"[rss_news] {feed['name']}: {len(items)} items")

    print(f"[rss_news] total fetched: {len(all_items)}")
    return all_items
