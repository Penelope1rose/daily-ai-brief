"""
Renderer — takes structured summary + weather data and generates docs/index.html.
"""

from __future__ import annotations
import html
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path


SGT = timezone(timedelta(hours=8))


def _esc(s: str) -> str:
    return html.escape(str(s or ""))


def _items_html(items: list[dict]) -> str:
    out = []
    for item in items:
        tag_html = f'<span class="item-chip">{_esc(item.get("tag",""))}</span>' if item.get("tag") else ""
        url = item.get("url", "")
        title_html = (
            f'<a href="{_esc(url)}" target="_blank" rel="noopener">{_esc(item.get("title",""))}</a>'
            if url else _esc(item.get("title", ""))
        )
        out.append(f"""
        <div class="item">
          <div class="item-title">{title_html}</div>
          <div class="item-desc">{_esc(item.get("summary",""))}</div>
          {tag_html}
        </div>""")
    return "\n".join(out)


def _weather_html(w: dict) -> str:
    forecast_html = "".join(f"""
        <div class="forecast-item">
          <div class="forecast-period">{_esc(f["period"])}</div>
          <div class="forecast-icon">{_esc(f["icon"])}</div>
          <div class="forecast-temp">{_esc(f["temp"])}</div>
          <div class="forecast-desc">{_esc(f["desc"])}</div>
        </div>""" for f in w.get("forecast", []))

    live_badge = "🟢 Live" if w.get("live") else "⚠️ Estimate"
    return f"""
    <div class="weather-widget">
      <div class="weather-location">📍 Singapore &nbsp;·&nbsp; <span style="font-size:0.65rem;opacity:0.6">{live_badge}</span></div>
      <div class="weather-main-row">
        <div>
          <div class="weather-temp-big">{_esc(w.get("temp","--"))}<sup>°C</sup></div>
          <div class="weather-condition">{_esc(w.get("condition",""))}</div>
          <div style="font-size:0.72rem;opacity:0.65;margin-top:2px">Feels like {_esc(w.get("feels_like","--"))}°C</div>
        </div>
        <div class="weather-icon-big">{_esc(w.get("icon","🌤️"))}</div>
      </div>
      <div class="weather-stats">
        <div class="weather-stat"><div class="weather-stat-label">Humidity</div><div class="weather-stat-val">{_esc(w.get("humidity","--"))}</div></div>
        <div class="weather-stat"><div class="weather-stat-label">Wind</div><div class="weather-stat-val">{_esc(w.get("wind","--"))}</div></div>
        <div class="weather-stat"><div class="weather-stat-label">UV Index</div><div class="weather-stat-val">{_esc(w.get("uv","--"))}</div></div>
      </div>
      <div class="weather-forecast-row">{forecast_html}</div>
      <div class="weather-note-small"><a href="https://www.weather.gov.sg" target="_blank" style="color:rgba(255,255,255,0.45)">weather.gov.sg</a> for official forecast</div>
    </div>"""


STYLES = """
:root { color-scheme: light; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5;
  color: #1a1a2e;
  padding: 16px;
}
.header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 22px; margin-bottom: 16px;
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  border-radius: 14px; color: white;
}
.header h1 { font-size: 1.25rem; font-weight: 800; }
.header .sub { font-size: 0.73rem; opacity: 0.55; margin-top: 3px; }
.header .meta { text-align: right; font-size: 0.78rem; opacity: 0.75; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.grid-full { grid-column: 1 / -1; }
.card { background: white; border-radius: 12px; padding: 16px; border: 1px solid #e4e8ef; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 13px; padding-bottom: 11px; border-bottom: 1px solid #f2f4f7; }
.card-title { font-size: 0.72rem; font-weight: 800; color: #444; text-transform: uppercase; letter-spacing: 0.8px; }
.card-badge { margin-left: auto; font-size: 0.62rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.badge-blue { background: #e8f0fe; color: #1a56db; }
.badge-green { background: #dcfce7; color: #15803d; }
.badge-orange { background: #fff7ed; color: #c2410c; }
.badge-purple { background: #f3e8ff; color: #7c3aed; }
.badge-indigo { background: #eef2ff; color: #4338ca; }
.item { margin-bottom: 11px; padding-bottom: 11px; border-bottom: 1px solid #f5f5f7; }
.item:last-child { border: none; margin: 0; padding: 0; }
.item-title { font-weight: 700; font-size: 0.82rem; margin-bottom: 3px; line-height: 1.3; }
.item-title a { color: #1a1a2e; text-decoration: none; }
.item-title a:hover { color: #302b63; text-decoration: underline; }
.item-desc { font-size: 0.77rem; color: #666; line-height: 1.55; }
.item-chip { display: inline-block; font-size: 0.62rem; font-weight: 700; padding: 2px 7px; border-radius: 10px; margin-top: 4px; background: #f0f4ff; color: #3949ab; }
.stack-section { margin-bottom: 12px; }
.stack-section:last-child { margin-bottom: 0; }
.stack-label { font-size: 0.67rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.8px; color: #999; margin-bottom: 6px; }
.pill-row { display: flex; flex-wrap: wrap; gap: 5px; }
.pill { font-size: 0.73rem; font-weight: 500; padding: 3px 11px; border-radius: 20px; border: 1px solid; }
.pill-default { background: #f8f9ff; color: #3949ab; border-color: #c5cae9; }
.pill-hot { background: #fff7ed; color: #c2410c; border-color: #fed7aa; }
.pill-free { background: #dcfce7; color: #15803d; border-color: #bbf7d0; }
.weather-widget { border-radius: 12px; background: linear-gradient(160deg, #1a1a5e 0%, #1565c0 50%, #0288d1 100%); color: white; padding: 16px; }
.weather-location { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; margin-bottom: 4px; }
.weather-main-row { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; }
.weather-temp-big { font-size: 2.8rem; font-weight: 800; line-height: 1; letter-spacing: -2px; }
.weather-temp-big sup { font-size: 1.2rem; font-weight: 400; vertical-align: super; letter-spacing: 0; }
.weather-condition { font-size: 0.82rem; opacity: 0.85; margin-top: 4px; }
.weather-icon-big { font-size: 3.2rem; line-height: 1; }
.weather-stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 12px; }
.weather-stat { background: rgba(255,255,255,0.12); border-radius: 8px; padding: 8px; text-align: center; }
.weather-stat-label { font-size: 0.62rem; opacity: 0.65; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }
.weather-stat-val { font-size: 0.85rem; font-weight: 700; }
.weather-forecast-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; }
.forecast-item { background: rgba(255,255,255,0.1); border-radius: 8px; padding: 7px 6px; text-align: center; }
.forecast-period { font-size: 0.6rem; opacity: 0.65; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 4px; }
.forecast-icon { font-size: 1.2rem; margin-bottom: 3px; }
.forecast-temp { font-size: 0.78rem; font-weight: 700; }
.forecast-desc { font-size: 0.62rem; opacity: 0.75; margin-top: 2px; line-height: 1.3; }
.weather-note-small { font-size: 0.62rem; opacity: 0.5; margin-top: 8px; text-align: center; }
.stack-para { font-size: 0.82rem; color: #555; line-height: 1.65; }
.link-row { display: flex; align-items: center; padding: 7px 0; border-bottom: 1px solid #f5f5f7; gap: 10px; }
.link-row:last-child { border: none; }
.link-dot { width: 6px; height: 6px; border-radius: 50%; background: #c5cae9; flex-shrink: 0; }
.link-row a { font-size: 0.8rem; font-weight: 600; color: #302b63; text-decoration: none; }
.link-row a:hover { text-decoration: underline; }
.link-sub { font-size: 0.71rem; color: #aaa; margin-left: auto; }
.footer { text-align: center; font-size: 0.7rem; color: #bbb; margin-top: 14px; }
@media (max-width: 600px) {
  .grid { grid-template-columns: 1fr; }
  .grid-full { grid-column: 1; }
}
"""


def render(summary: dict, weather: dict, output_path: str = "docs/index.html") -> None:
    now_sgt = datetime.now(SGT)
    date_str = now_sgt.strftime("%A, %d %B %Y")
    time_str = now_sgt.strftime("%H:%M SGT")

    news_html = _items_html(summary.get("ai_news", []))
    tools_html = _items_html(summary.get("tools", []))
    usecases_html = _items_html(summary.get("use_cases", []))
    learning_html = _items_html(summary.get("learning", []))
    domain_html = _items_html(summary.get("domain_deepdive", []))
    stack_text = _esc(summary.get("stack_highlights", ""))
    weather_block = _weather_html(weather)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ray's Daily AI Brief — {_esc(date_str)}</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
<style>{STYLES}</style>
</head>
<body>

<div class="header">
  <div>
    <h1>🤖 Ray's Daily AI Brief</h1>
    <div class="sub">Singapore · AI Engineer · Auto-updated daily at 8 AM SGT</div>
  </div>
  <div class="meta">{_esc(date_str)}<br>{_esc(time_str)}</div>
</div>

<div class="grid">

  <div class="card">
    <div class="card-header">
      <span>📰</span>
      <span class="card-title">AI News & Releases</span>
      <span class="card-badge badge-blue">THIS WEEK</span>
    </div>
    {news_html}
  </div>

  <div class="card">
    <div class="card-header">
      <span>🛠️</span>
      <span class="card-title">Tools to Try</span>
      <span class="card-badge badge-green">FREE TIER</span>
    </div>
    {tools_html}
  </div>

  <div class="card">
    <div class="card-header">
      <span>💡</span>
      <span class="card-title">AI Use Cases & Projects</span>
      <span class="card-badge badge-orange">TRENDING</span>
    </div>
    {usecases_html}
  </div>

  <div class="card">
    <div class="card-header">
      <span>📚</span>
      <span class="card-title">Learning & Certifications</span>
      <span class="card-badge badge-purple">POPULAR</span>
    </div>
    {learning_html}
  </div>

  <div class="card grid-full">
    <div class="card-header">
      <span>⚡</span>
      <span class="card-title">Stack Highlights · Solo Devs & AI Engineers</span>
      <span class="card-badge badge-green">INDIE FRIENDLY</span>
    </div>
    <p class="stack-para">{stack_text}</p>
  </div>

  <div class="card">
    <div class="card-header">
      <span>🔬</span>
      <span class="card-title">Domain Deep-Dive · RAG & Agents</span>
      <span class="card-badge badge-indigo">YOUR STACK</span>
    </div>
    {domain_html}
  </div>

  <div class="card">
    <div class="card-header">
      <span>🌤️</span>
      <span class="card-title">Weather · Singapore</span>
    </div>
    {weather_block}
  </div>

  <div class="card grid-full">
    <div class="card-header">
      <span>🔗</span>
      <span class="card-title">Quick Links</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0 20px">
      <div>
        <div class="link-row"><div class="link-dot"></div><a href="https://news.ycombinator.com" target="_blank">Hacker News</a><span class="link-sub">Tech & AI discussions</span></div>
        <div class="link-row"><div class="link-dot"></div><a href="https://huggingface.co/papers" target="_blank">HuggingFace Papers</a><span class="link-sub">Daily ML papers</span></div>
      </div>
      <div>
        <div class="link-row"><div class="link-dot"></div><a href="https://github.com/trending?l=python" target="_blank">GitHub Trending (Python)</a><span class="link-sub">Hottest repos</span></div>
        <div class="link-row"><div class="link-dot"></div><a href="https://paperswithcode.com" target="_blank">Papers With Code</a><span class="link-sub">Research + code</span></div>
      </div>
      <div>
        <div class="link-row"><div class="link-dot"></div><a href="https://www.reddit.com/r/LocalLLaMA/" target="_blank">r/LocalLLaMA</a><span class="link-sub">Open-source LLM community</span></div>
        <div class="link-row"><div class="link-dot"></div><a href="https://www.deeplearning.ai" target="_blank">DeepLearning.AI</a><span class="link-sub">Short courses, free</span></div>
      </div>
    </div>
  </div>

</div>

<div class="footer">
  Generated by <strong>daily-ai-brief</strong> · Sources: HackerNews · Reddit · ArXiv · GitHub · DEV.to · wttr.in · Gemini 2.0 Flash
</div>

</body>
</html>"""

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"[renderer] written to {output_path}")
