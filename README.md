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

This script:

- Starts **Postgres** with `docker compose up -d postgres` (skipped with `./scripts/run-dev.sh --no-docker` if you use SQLite or manage Postgres yourself).
- Ensures **`api/.env`** exists (copies `.env.example` once) and **`web/.env.local`** points `NEXT_PUBLIC_API_URL` at the API.
- Creates **`api/.venv`**, installs Python deps, installs **web** deps if needed.
- Runs **uvicorn** (reload) and **`npm run dev`** together until you press **Ctrl+C** (containers are left running unless you stop them separately).

Ports: **`API_PORT`** (default `8000`), **`WEB_PORT`** (default `3000`).

Open [http://localhost:3000](http://localhost:3000) (UI) and [http://localhost:8000/docs](http://localhost:8000/docs) (OpenAPI).

### Manual breakdown (optional)

If you prefer three terminals: start Postgres (`docker compose up -d postgres`), run `uvicorn` from `api/` with `app.main:app`, and `npm run dev` from `web/`. Copy `.env.example` → `api/.env` and set `web/.env.local` as needed.

## API

- Versioned routes: `POST /api/v1/chat/insights`, `GET /api/v1/analytics/summary`, etc.
- Legacy: `POST /chat/insights` (same payload as v1).
- **CORS:** set `CORS_ORIGINS` (comma-separated, or `*` for dev). Example: `http://localhost:3000`.

## Deployment sketch

- **Frontend:** Vercel project root = `web/`, env `NEXT_PUBLIC_API_URL` = your API origin.
- **Backend:** any container host (Railway, Fly, etc.); use `api/Dockerfile` with **repository root** as build context (see `docker-compose.prod.yml`).

## Data / embeddings

Default paths under process working directory: `data/raw_docs`, `data/embeddings` (FAISS). Mount a volume in production so indexes persist.
