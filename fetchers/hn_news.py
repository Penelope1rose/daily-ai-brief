"""
HackerNews Algolia API — fetches recent AI/ML stories.
Free, no API key required.
"""

import requests
from datetime import datetime, timedelta, timezone


def fetch(max_items: int = 20) -> list[dict]:
    """Return recent HN stories mentioning AI/ML."""
    queries = ["artificial intelligence", "LLM", "RAG", "machine learning", "GPT", "Claude AI"]
    items = {}
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)

    for query in queries:
        try:
            resp = requests.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "tags": "story",
                    "query": query,
                    "hitsPerPage": 10,
                    "numericFilters": f"created_at_i>{int(cutoff.timestamp())}",
                },
                timeout=10,
            )
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
                if hit["objectID"] not in items:
                    items[hit["objectID"]] = {
                        "title": hit.get("title", ""),
                        "url": url,
                        "source": "Hacker News",
                        "snippet": f"HN score: {hit.get('points', 0)} | comments: {hit.get('num_comments', 0)}",
                    }
        except Exception as e:
            print(f"[hn_news] query '{query}' failed: {e}")

    result = list(items.values())[:max_items]
    print(f"[hn_news] fetched {len(result)} items")
    return result
