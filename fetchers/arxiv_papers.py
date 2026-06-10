"""
ArXiv API — latest AI/ML papers.
Free, no API key required.
"""

import requests
import xml.etree.ElementTree as ET


ARXIV_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch(max_items: int = 10) -> list[dict]:
    """Return the most recently submitted AI/ML papers."""
    try:
        resp = requests.get(
            ARXIV_URL,
            params={
                "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": max_items,
            },
            timeout=15,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        items = []
        for entry in root.findall("atom:entry", NS):
            title = entry.findtext("atom:title", namespaces=NS, default="").strip().replace("\n", " ")
            summary = entry.findtext("atom:summary", namespaces=NS, default="").strip()[:300]
            link_el = entry.find("atom:link[@rel='alternate']", NS) or entry.find("atom:link", NS)
            url = link_el.get("href", "") if link_el is not None else ""
            items.append({
                "title": title,
                "url": url,
                "source": "ArXiv",
                "snippet": summary,
            })
        print(f"[arxiv] fetched {len(items)} papers")
        return items
    except Exception as e:
        print(f"[arxiv] failed: {e}")
        return []
