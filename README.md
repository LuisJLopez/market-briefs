# Market Briefs

A scheduled bot that posts AI-generated financial market commentary to X/Twitter throughout the trading day. It uses OpenAI GPT-4o (configurable) to produce concise, professional tweets for each market session — US open/close, UK open/close, liquidity, gold, sentiment, and weekend briefings.

Designed to run continuously on Google Cloud Run with no manual intervention.

---

## Project structure

```
market-briefs/
├── src/
│   ├── main.py             # Entry point: starts scheduler + HTTP health server
│   ├── scheduler.py        # APScheduler cron jobs for each market session
│   ├── processor.py        # Orchestrates prompt → tweet pipeline per job
│   ├── openai_prompter.py  # Builds prompts and calls the OpenAI Chat API
│   ├── tweet.py            # Authenticates with X and posts tweets via Tweepy
│   └── config.py           # Loads env vars, timezone objects, and logging
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── logs/                   # Runtime log output (git-ignored)
```

## How it works

1. **`main.py`** spawns the scheduler in a background thread and starts a minimal HTTP server for Cloud Run health checks.
2. **`scheduler.py`** registers all jobs with APScheduler using `CronTrigger`, each mapped to a market session key.
3. **`processor.py`** receives the session key, calls the `Prompter` to generate a tweet, then posts it via `Tweeter`.
4. **`openai_prompter.py`** builds the prompt using a two-message architecture (system: persona + hard rules; user: topic + few-shot style examples) and calls the OpenAI Chat API. The model is configurable via `OPENAI_MODEL` (default: `gpt-4o`).
5. **`tweet.py`** authenticates with the X API via OAuth 1.0a (Tweepy) and calls `create_tweet`.

Logs are written to `logs/tweet_bot.log` and streamed to stdout.

---

## Prompt design

Each session uses a two-message prompt structure:

- **System message** — stable persona, hard formatting rules, and a banned-phrases list (e.g. "Stay tuned", "keep an eye on") that prevent the model from producing generic bot-sounding output.
- **User message** — a session-specific description followed by **3 tailored few-shot example tweets** for that exact time slot.

The few-shot examples are the core of the approach. A UK pre-open tweet, a gold update, and an earnings preview should each have a distinct voice, focus, and structure — one shared example block produces generic output. Each section has examples that demonstrate the correct tone, unicode bold usage, emoji count (1–2 max), and content focus for that slot.

To adjust tweet style or add a new session, edit `_SESSIONS` in `src/openai_prompter.py`.

---

## Scheduled jobs

All times are local to the specified timezone. Weekday jobs run Mon–Fri only.

| Job | Time | Timezone | Section key |
|-----|------|----------|-------------|
| US pre-open | 08:30 | America/New_York | `us_pre_open` |
| US post-close | 16:30 | America/New_York | `us_post_close` |
| UK pre-open | 07:00 | Europe/London | `uk_pre_open` |
| UK close | 16:30 | Europe/London | `uk_close` |
| M2 liquidity | 08:30 | Europe/London | `liquidity` |
| Gold | 19:00 | Europe/London | `gold` |
| Market sentiment | 14:00 | Europe/London | `market_sentiment` |
| NBIS / big-tech buys | 12:00 | Europe/London | `nbis` |
| Saturday briefing | Sat 23:40 | Europe/London | `test_event` |
| Sunday briefing | Sun 10:00 | Europe/London | `sunday_briefing` |
| Sunday earnings preview | Sun 13:00 | Europe/London | `sunday_earning` |

---

## Setup

### Prerequisites

- Python 3.11+
- [OpenAI API key](https://platform.openai.com/api-keys) with GPT-4o access (or set `OPENAI_MODEL` to any model your key supports)
- [X/Twitter developer app](https://developer.twitter.com/en/portal) with **Read + Write** permissions and OAuth 1.0a user tokens

### Local development

```bash
# Clone and enter the repo
git clone https://github.com/LuisJLopez/market-briefs.git
cd market-briefs

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Open .env and fill in your API keys

# Export env vars, then run
export $(grep -v '^#' .env | xargs)
python src/main.py
```

### Docker

```bash
cp .env.example .env
# Fill in .env

docker build -t market-briefs .
docker run --env-file .env -p 8080:8080 market-briefs
```

### Docker Compose

```bash
cp .env.example .env
# Fill in .env

docker compose up --build
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `X_API_KEY` | Yes | X/Twitter consumer key |
| `X_API_SECRET` | Yes | X/Twitter consumer secret |
| `X_ACCESS_TOKEN` | Yes | X/Twitter access token |
| `X_ACCESS_TOKEN_SECRET` | Yes | X/Twitter access token secret |
| `OPENAI_MODEL` | No | Model to use (default: `gpt-4o`). Options: `gpt-4o`, `gpt-4.1`, `gpt-4o-mini` |
| `PORT` | No | HTTP health check port (default: `8080`) |
| `LOG_DIR` | No | Directory for `tweet_bot.log` (default: `logs/`) |

---

## Deployment (Google Cloud Run)

```bash
gcloud run deploy market-briefs \
  --source . \
  --region europe-west1 \
  --set-env-vars "OPENAI_API_KEY=sk-...,X_API_KEY=...,X_API_SECRET=...,X_ACCESS_TOKEN=...,X_ACCESS_TOKEN_SECRET=..." \
  --min-instances 1
```

> Use `--min-instances 1` to prevent Cloud Run from scaling to zero — the scheduler must stay alive between jobs.

For production, prefer storing secrets in [Google Secret Manager](https://cloud.google.com/secret-manager) and referencing them via `--set-secrets` instead of plain `--set-env-vars`.

---

## License

MIT
