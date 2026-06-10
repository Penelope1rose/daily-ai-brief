"""
DEV.to API — recent AI articles.
Free, no API key required.
"""

import requests

TAGS = ["ai", "machinelearning", "llm", "python"]


def fetch(max_items: int = 10) -> list[dict]:
    """Return recent AI articles from DEV.to."""
    items = {}
    for tag in TAGS:
        try:
            resp = requests.get(
                "https://dev.to/api/articles",
                params={"tag": tag, "per_page": 4, "top": 1},
                timeout=10,
            )
            resp.raise_for_status()
            for art in resp.json():
                if art["id"] not in items:
                    items[art["id"]] = {
                        "title": art.get("title", ""),
                        "url": art.get("url", ""),
                        "source": "DEV.to",
                        "snippet": art.get("description", "") or "",
                    }
        except Exception as e:
            print(f"[devto] tag '{tag}' failed: {e}")

    result = list(items.values())[:max_items]
    print(f"[devto] fetched {len(result)} articles")
    return result
