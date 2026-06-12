# FIFA 2026 Football Intelligence Agent

An early vertical slice for a FIFA World Cup 2026 assistant. It combines:

- A FastAPI backend.
- `uv` for Python dependency management.
- An OpenAI Agents SDK integration path with a deterministic local fallback.
- A transparent match prediction engine.
- A CSV benchmark runner for prediction quality.
- A Telegram webhook entrypoint.
- A small Next.js UI scaffold managed with `bun`.
- Docker Compose for local containerized runs.

The first implementation uses mock football data so the app can run before paid/live sports APIs are selected.

## Repository Structure

```text
backend/
  app/
    agents/          Agent orchestration and fallback routing
    data/            Mock data provider
    prediction/      Prediction engine, metrics, and CSV benchmark
    telegram/        Telegram webhook handling
    tools/           Reusable football tools
    main.py          FastAPI app

data/
  benchmarks/        Historical match benchmark CSVs

frontend/
  app/               Next.js App Router UI
  lib/               Typed API client

reports/             Generated benchmark reports
tests/               Backend unit tests
```

## Backend Setup

```bash
uv sync
cp .env.example .env
uv run uvicorn backend.app.main:app --reload --port 8010
```

Health check:

```bash
curl http://localhost:8010/health
```

Prediction example:

```bash
curl -X POST http://localhost:8010/predict \
  -H "Content-Type: application/json" \
  -d '{"team_a":"Brazil","team_b":"Germany"}'
```

Chat example:

```bash
curl -X POST http://localhost:8010/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"/predict Brazil vs Germany","channel":"web"}'
```

## Benchmark

Run the seeded CSV benchmark:

```bash
uv run python -m backend.app.prediction.benchmark
```

This writes:

```text
reports/prediction_benchmark_report.csv
```

The benchmark must only include features known before kickoff. Do not include post-match or final tournament information in historical rows.

## Relai Tools

These commands are JSON-first so Relai, CI, or any scheduler can run them safely.

Refresh the local World Cup 2026 match cache:

```bash
uv run python -m backend.app.relai_tools sync
```

Check whether cached match data is fresh:

```bash
uv run python -m backend.app.relai_tools freshness --max-age-minutes 60 --fail-on-stale
```

Run prediction benchmarks:

```bash
uv run python -m backend.app.relai_tools benchmark
```

Run lightweight smoke checks:

```bash
uv run python -m backend.app.relai_tools smoke
```

Suggested Relai schedule:

```text
Every 15 minutes: sync
Every 15 minutes after sync: freshness --fail-on-stale
On every deploy: smoke + benchmark
```

The backend also exposes:

```text
GET /data/freshness
```

## Frontend Setup

```bash
cd frontend
bun install
NEXT_PUBLIC_API_URL=http://localhost:8010 bun run dev
```

Open:

```text
http://localhost:3010
```

## Docker Setup

Create `.env` first:

```bash
cp .env.example .env
```

Run both services:

```bash
docker compose up --build
```

For hot reload while developing:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

This runs Uvicorn with `--reload` and Next.js with `next dev`, with the local `backend/`, `data/`, and `frontend/` directories mounted into the containers. Backend code/data edits restart the API process, and frontend edits are reflected by the Next dev server. Rebuild the dev stack after changing `pyproject.toml`, `uv.lock`, `frontend/package.json`, or `frontend/bun.lock`.

Services:

```text
Backend:  http://localhost:8010
Frontend: http://localhost:3010
```

The frontend Docker image bakes `NEXT_PUBLIC_API_URL` at build time. The default Compose value points browser traffic at `http://localhost:8010`.

If `/chat` returns a CORS preflight error, set `ALLOWED_ORIGINS` to the exact browser origin you are using:

```bash
ALLOWED_ORIGINS=http://localhost:3010,http://127.0.0.1:3010
```

For a tunnel or hosted frontend, append that URL too:

```bash
ALLOWED_ORIGINS=http://localhost:3010,https://your-frontend-domain.example
```

## Telegram Setup

1. Create a bot with BotFather.
2. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WEBHOOK_SECRET` to `.env`.
3. Deploy the backend behind HTTPS.
4. Register the webhook:

```bash
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=$PUBLIC_BASE_URL/telegram/webhook" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"
```

For local testing, keep the webhook handler but use a tunnel such as ngrok or Cloudflare Tunnel.

## Current Scope

Implemented now:

- Explainable baseline prediction model.
- Seed CSV benchmark and report generation.
- FastAPI chat and prediction endpoints.
- Optional OpenAI Agents SDK integration path.
- Telegram webhook handling.
- Minimal Next.js dashboard.
- Unit tests for prediction and benchmark behavior.
- `uv` backend lockfile and `bun` frontend lockfile.
- Backend and frontend Dockerfiles with Docker Compose.
- Relai-friendly sync, freshness, benchmark, and smoke commands.

Next useful steps:

- Add a real sports data provider behind `FootballTools`.
- Replace mock standings and schedule with API-backed data.
- Add shadcn/Radix components once UI patterns stabilize.
- Add persistence for Telegram subscriptions and user favorites.
