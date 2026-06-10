"""
main.py — orchestrates the daily AI brief pipeline.

Usage:
  python main.py              # generates docs/index.html
  python main.py --dry-run    # fetch only, skip LLM + render (for testing APIs)
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from fetchers import hn_news, arxiv_papers, github_trending, devto, weather, rss_news
from summarizer import summarize
from renderer import render


def fetch_all() -> tuple[list[dict], dict]:
    """Fetch all data sources in parallel. Returns (items, weather_data)."""
    all_items = []
    weather_data = {}

    tasks = {
        "hn":      lambda: hn_news.fetch(max_items=20),
        "arxiv":   lambda: arxiv_papers.fetch(max_items=10),
        "github":  lambda: github_trending.fetch(max_items=8),
        "devto":   lambda: devto.fetch(max_items=10),
        "rss":     lambda: rss_news.fetch(max_per_feed=8),
        "weather": lambda: weather.fetch(),
    }

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if name == "weather":
                    weather_data = result
                else:
                    all_items.extend(result)
            except Exception as e:
                print(f"[main] fetcher '{name}' raised: {e}")

    print(f"[main] total items fetched: {len(all_items)}")
    return all_items, weather_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Fetch only, skip summarizer + renderer")
    parser.add_argument("--output", default="docs/index.html", help="Output HTML path")
    args = parser.parse_args()

    print("=== Daily AI Brief Pipeline ===")

    items, weather_data = fetch_all()

    if args.dry_run:
        print("[main] dry-run: skipping summarizer and renderer")
        print(f"[main] sample items: {[i['title'] for i in items[:5]]}")
        return

    if not items:
        print("[main] no items fetched — aborting")
        sys.exit(1)

    summary = summarize(items)
    render(summary, weather_data, output_path=args.output)

    print(f"[main] done → {args.output}")


if __name__ == "__main__":
    main()
