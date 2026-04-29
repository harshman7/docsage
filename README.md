# DocSage

Agentic RAG stack for document intelligence (IDP-inspired): **FastAPI + LangGraph** backend, **Next.js** frontend (Vercel-friendly), **PostgreSQL**, and **FAISS** embeddings. The app uses **Google Gemini** (Generative Language API) for all LLM calls.

## Layout

| Path | Role |
|------|------|
| `api/` | Python app (`app` package), `requirements.txt`, `Dockerfile` |
| `web/` | Next.js 14 (App Router) UI |
| `scripts/run-dev.sh` | Local dev: optional Postgres (Docker), API + web |
| `docker-compose.postgres.yml` | Postgres-only Compose (used by the dev script) |
| `docker-compose.yml` | Postgres + API (full stack in containers) |
| `docker-compose.prod.yml` | Production-oriented Compose example |

## Prerequisites

- **Node.js** (for `web/`) and **Python 3.11+** (for `api/`)
- **Docker** (optional): for Postgres via Compose, or run with **SQLite** for a quick local DB
- **Google AI Studio API key** for chat, insights, and other LLM features: create one at [Google AI Studio](https://aistudio.google.com/apikey)

## Quick start (local)

From the **repository root**:

```bash
./scripts/run-dev.sh
```

This uses [`docker-compose.postgres.yml`](docker-compose.postgres.yml) to start **Postgres only** (your Gemini key is not needed for that step). If Docker is not running, Postgres is skipped and the API + web still start; set `USE_SQLITE=true` in `api/.env`, or start **Docker Desktop** and run the script again.

The script also:

- Ensures **`api/.env`** exists (copies [`.env.example`](.env.example) on first run) and **`web/.env.local`** sets `NEXT_PUBLIC_API_URL` to the API.
- Creates **`api/.venv`**, installs Python dependencies, and **web** `node_modules` if missing.
- Runs **uvicorn** (reload) and **`npm run dev`** until **Ctrl+C** (the Postgres container keeps running if it was started).

Pass **`--no-docker`** to skip starting Postgres entirely.

**Ports:** `API_PORT` (default `8000`), `WEB_PORT` (default `3000`). Open [http://localhost:3000](http://localhost:3000) and [http://localhost:8000/docs](http://localhost:8000/docs).

If host port **5432** is already in use:

```bash
POSTGRES_PORT=5433 ./scripts/run-dev.sh
```

…and set `POSTGRES_PORT=5433` in `api/.env` so the API connects to the mapped port.

### Without the dev script

Start Postgres with `docker compose -f docker-compose.postgres.yml up -d` (or use SQLite). From `api/`, run `uvicorn app.main:app --reload` (with `api/.env` present). From `web/`, run `npm run dev`. Point `web/.env.local` at your API URL.

## Configuration

Copy [`.env.example`](.env.example) to **`api/.env`** and set:

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key (alias: `GEMINI_API_KEY`) |
| `GOOGLE_AI_MODEL` | Model id for `generateContent` (default: `gemini-3.1-flash-lite-preview`) |
| `POSTGRES_*` | Database connection when using Postgres |
| `USE_SQLITE` | Set `true` to use SQLite instead of Postgres |
| `CORS_ORIGINS` | Comma-separated browser origins, or `*` (dev only) |

The **web** app expects `NEXT_PUBLIC_API_URL` (e.g. `http://127.0.0.1:8000`) in `web/.env.local`; the dev script creates this if the file is missing.

**Docker Compose** (`docker-compose.yml` / `docker-compose.prod.yml`): pass `GOOGLE_API_KEY` (and optionally `GOOGLE_AI_MODEL`) into the `api` service environment so LLM routes work inside the container.

## LLM

All text generation goes through **Gemini** via the [Generative Language API](https://ai.google.dev/api) (`generateContent`). There is no separate Groq, Ollama, or Hugging Face LLM integration in this repo.

## API

- Versioned routes: `POST /api/v1/chat/insights`, `GET /api/v1/analytics/summary`, and related endpoints under `/api/v1/`.
- Legacy: `POST /chat/insights` (same payload as v1).
- **CORS:** configure `CORS_ORIGINS` in `api/.env`.

## Frontend

Next.js App Router UI with light/dark theme (sidebar and marketing pages). Light mode uses `/logo.png`; dark mode uses `/logo-dark.png` in `web/public/`.

## Deployment (sketch)

- **Frontend:** deploy `web/` (e.g. Vercel); set `NEXT_PUBLIC_API_URL` to your API origin.
- **Backend:** run `api/Dockerfile` with **repository root** as build context; inject `GOOGLE_API_KEY` and database settings. See [`docker-compose.prod.yml`](docker-compose.prod.yml) for an example shape.

## Data / embeddings

Default paths (relative to the process working directory): `data/raw_docs`, `data/embeddings` (FAISS). Mount a volume in production so indexes and raw uploads persist.
