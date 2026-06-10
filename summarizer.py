"""
Summarizer — sends raw fetched data to Gemini 2.0 Flash and returns
structured categories for the dashboard.
"""

import json
import os
import re

from google import genai
from google.genai import types


PROMPT_TEMPLATE = """
You are an AI news curator for a senior AI Engineer based in Singapore (4+ years experience, builds RAG pipelines, LLM apps, agentic AI systems). He is technically strong — do not explain basics.

Below is raw data fetched today from HackerNews, Reddit, ArXiv, GitHub, and DEV.to.
Analyze it and return a single JSON object with these exact keys:

{{
  "ai_news": [
    {{"title": "...", "summary": "...", "url": "...", "tag": "..."}}
  ],
  "tools": [
    {{"title": "...", "summary": "...", "url": "...", "tag": "..."}}
  ],
  "use_cases": [
    {{"title": "...", "summary": "...", "url": "...", "tag": "..."}}
  ],
  "learning": [
    {{"title": "...", "summary": "...", "url": "...", "tag": "..."}}
  ],
  "stack_highlights": "...",
  "domain_deepdive": [
    {{"title": "...", "summary": "...", "url": "...", "tag": "..."}}
  ]
}}

Rules:
- ai_news: top 5 items — model releases, company news, research breakthroughs. Prioritise recency.
- tools: top 5 — AI tools with free/indie tier worth trying. Practical for solo devs / AI engineers.
- use_cases: top 5 — what people are actively building with AI right now. Include GitHub links, youtube links or social media video links where available.
- learning: top 3 — courses, certs, tutorials. Include free options. Mention provider + cost. If available in Coursera, most preferred.
- stack_highlights: 3–4 sentence paragraph. Cover trending databases (vector + relational), AI platforms, cloud/hosting, automation tools. Solo-dev / indie angle — no enterprise-only tools.
- domain_deepdive: top 3 — specific to RAG, LLM agents, LangChain/LlamaIndex, LLM tooling, agentic frameworks.
- Each summary: max 2 direct sentences. Technical depth — no fluff.
- Use real URLs from the data. If a category lacks data, draw on your knowledge for recent items but flag with url = "".
- Tags: "Model Release", "Open Source", "Research", "Agent", "RAG", "Tool", "Automation", "Free", "Cert", "Framework"

Return ONLY the raw JSON object. No markdown, no explanation, no code fences.

RAW DATA:
{data}
"""


# Models tried in order — falls back if quota is hit on primary.
# Ordered by RPD limit (highest first). gemini-2.0-flash has 0 quota on free tier.
MODELS = [
    "gemini-3.1-flash-lite",   # 500 RPD free tier — primary
    "gemini-2.5-flash",        # 20 RPD free tier
    "gemini-2.5-flash-lite",   # 20 RPD free tier
    "gemini-3.5-flash",        # 20 RPD free tier
    "gemini-3.0-flash",        # 20 RPD free tier
]


def summarize(all_items: list[dict]) -> dict:
    """Send all fetched items to Gemini and return structured categories."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)

    # Trim to avoid token limits — keep 60 items max
    trimmed = all_items[:60]
    data_str = json.dumps(trimmed, ensure_ascii=False, indent=2)

    prompt = PROMPT_TEMPLATE.replace("{data}", data_str)

    last_error = None
    for model in MODELS:
        try:
            print(f"[summarizer] trying {model} with {len(trimmed)} items...")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
                ),
            )
            raw = response.text.strip()
            break  # success
        except Exception as e:
            print(f"[summarizer] {model} failed: {e}")
            last_error = e
    else:
        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

    raw = response.text.strip()

    # Robust JSON extraction
    def extract_json(text: str) -> dict:
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Strip markdown fences
        fence = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if fence:
            try:
                return json.loads(fence.group(1))
            except json.JSONDecodeError:
                pass
        # Extract first {...}
        brace = re.search(r"(\{[\s\S]*\})", text)
        if brace:
            try:
                return json.loads(brace.group(1))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Could not extract JSON from response:\n{text[:500]}")

    result = extract_json(raw)
    print("[summarizer] done")
    return result
