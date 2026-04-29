# DocSage

Agentic RAG stack for document intelligence (IDP-inspired): **FastAPI + LangGraph** backend, **Next.js** frontend (Vercel-friendly), **PostgreSQL**, **FAISS** embeddings.

## Layout

| Path | Role |
|------|------|
| `api/` | Python app (`app` package), `requirements.txt`, `Dockerfile`, scripts |
| `web/` | Next.js 14 (App Router) UI |
| `docker-compose.yml` | Postgres + optional API container (API image built from repo root) |

## Quick start (local)

From the **repository root**:

```bash
./scripts/run-dev.sh
```

Uses [`docker-compose.postgres.yml`](docker-compose.postgres.yml) for Postgres only (so `GOOGLE_API_KEY` is not required for that step). If Docker is not running, Postgres is skipped and the API + web still start; use `USE_SQLITE=true` in `api/.env`, or start **Docker Desktop** and run the script again.

The script also:

- Ensures **`api/.env`** exists (copies `.env.example` once) and **`web/.env.local`** points `NEXT_PUBLIC_API_URL` at the API.
- Creates **`api/.venv`**, installs Python deps, installs **web** deps if needed.
- Runs **uvicorn** (reload) and **`npm run dev`** together until you press **Ctrl+C** (Postgres container keeps running if it was started).

Pass **`--no-docker`** to skip starting Postgres entirely.

Ports: **`API_PORT`** (default `8000`), **`WEB_PORT`** (default `3000`).
Open [http://localhost:3000](http://localhost:3000) (UI) and [http://localhost:8000/docs](http://localhost:8000/docs) (OpenAPI).

### Manual breakdown (optional)

Start Postgres with `docker compose -f docker-compose.postgres.yml up -d`, then run `uvicorn` from `api/` (`app.main:app`) and `npm run dev` from `web/`. Copy `.env.example` → `api/.env` and set `web/.env.local` as needed.

## API

- Versioned routes: `POST /api/v1/chat/insights`, `GET /api/v1/analytics/summary`, etc.
- Legacy: `POST /chat/insights` (same payload as v1).
- **CORS:** set `CORS_ORIGINS` (comma-separated, or `*` for dev). Example: `http://localhost:3000`.

## Deployment sketch

- **Frontend:** Vercel project root = `web/`, env `NEXT_PUBLIC_API_URL` = your API origin.
- **Backend:** any container host (Railway, Fly, etc.); use `api/Dockerfile` with **repository root** as build context (see `docker-compose.prod.yml`).

## Data / embeddings

Default paths under process working directory: `data/raw_docs`, `data/embeddings` (FAISS). Mount a volume in production so indexes persist.
