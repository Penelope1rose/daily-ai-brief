"""
GitHub Search API — trending AI/ML repositories.
Free with optional GITHUB_TOKEN for higher rate limits (5000 req/hr vs 60).
"""

import os
import requests
from datetime import datetime, timedelta, timezone


def fetch(max_items: int = 8) -> list[dict]:
    """Return recently-starred AI/ML repos."""
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    topics = ["llm", "rag", "ai-agent", "langchain", "transformers"]
    items = {}

    for topic in topics:
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": f"topic:{topic} pushed:>{since}",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 3,
                },
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            for repo in resp.json().get("items", []):
                if repo["full_name"] not in items:
                    items[repo["full_name"]] = {
                        "title": f"{repo['full_name']} ⭐{repo['stargazers_count']:,}",
                        "url": repo["html_url"],
                        "source": "GitHub",
                        "snippet": repo.get("description", "") or "",
                    }
        except Exception as e:
            print(f"[github] topic '{topic}' failed: {e}")

    result = list(items.values())[:max_items]
    print(f"[github] fetched {len(result)} repos")
    return result
