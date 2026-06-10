"""
Reddit JSON API — hot posts from ML/AI subreddits.
Free, no API key required (uses public JSON endpoint).
"""

import requests

SUBREDDITS = ["MachineLearning", "LocalLLaMA", "artificial"]
HEADERS = {"User-Agent": "DailyAIBrief/1.0 (personal dashboard)"}


def fetch(max_per_sub: int = 5) -> list[dict]:
    """Return hot posts from AI/ML subreddits."""
    items = []
    for sub in SUBREDDITS:
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{sub}/hot.json",
                params={"limit": max_per_sub},
                headers=HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])
            for post in posts:
                d = post["data"]
                if d.get("is_self") and not d.get("selftext"):
                    continue
                items.append({
                    "title": d.get("title", ""),
                    "url": f"https://reddit.com{d.get('permalink', '')}",
                    "source": f"r/{sub}",
                    "snippet": (d.get("selftext", "") or d.get("url", ""))[:200],
                })
        except Exception as e:
            print(f"[reddit] r/{sub} failed: {e}")

    print(f"[reddit] fetched {len(items)} items")
    return items
