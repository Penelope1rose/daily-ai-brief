# 🤖 Daily AI Brief

A self-hosted morning dashboard that fetches live AI news, tools, papers, and projects daily — summarised by Gemini 2.0 Flash into clean categorised cards. Runs automatically at **8 AM SGT** via GitHub Actions and publishes to GitHub Pages.

## What's inside each brief

| Section | Sources |
|---|---|
| 📰 AI News & Releases | HackerNews, Reddit, DEV.to |
| 🛠️ Tools to Try (free tier) | HackerNews, GitHub, DEV.to |
| 💡 Use Cases & Projects | GitHub Trending, Reddit |
| 📚 Learning & Certifications | DEV.to, Reddit, HackerNews |
| ⚡ Stack Highlights | Synthesised by LLM |
| 🔬 Domain Deep-Dive (RAG/Agents) | ArXiv, GitHub, Reddit |
| 🌤️ Weather · Singapore | wttr.in (live) |

## Setup

### 1. Fork / clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/daily-ai-brief.git
cd daily-ai-brief
```

### 2. Get a Gemini API key (free)

Go to [Google AI Studio](https://aistudio.google.com/app/apikey) → Create API key.
No credit card required. Free tier: 1,500 requests/day.

### 3. Add secrets to GitHub

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key |
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions — no action needed |

Optionally add a personal `GITHUB_TOKEN` for higher API rate limits (5,000/hr vs 60/hr).

### 4. Enable GitHub Pages

Go to **Settings → Pages** → Source: **Deploy from a branch** → Branch: `main` → Folder: `/docs` → Save.

Your dashboard URL will be: `https://YOUR_USERNAME.github.io/daily-ai-brief`

### 5. Trigger first run

Go to **Actions → Daily AI Brief → Run workflow** to generate your first brief immediately.
After that it runs automatically every day at 8 AM SGT.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env with your GEMINI_API_KEY

python main.py                  # generate docs/index.html
python main.py --dry-run        # test fetchers only (no API call)
open docs/index.html            # view in browser
```

## Customisation

- **Add/remove sources**: edit `fetchers/` — each file is independent
- **Change categories or tone**: edit the prompt in `summarizer.py`
- **Change schedule**: edit `cron` in `.github/workflows/daily_brief.yml`
  - 8 AM SGT = `0 0 * * *` (UTC)
  - 7 AM SGT = `59 23 * * *` (UTC previous day)

## Tech stack

- **LLM**: [Gemini 2.0 Flash](https://ai.google.dev/) — free tier, best hallucination score on summarisation benchmarks
- **Sources**: HackerNews Algolia · Reddit JSON · ArXiv · GitHub Search · DEV.to · wttr.in — all free, no auth required
- **CI/CD**: GitHub Actions
- **Hosting**: GitHub Pages (free)
- **Cost**: $0
