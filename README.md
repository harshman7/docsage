# DocSage

Agentic RAG stack for document intelligence (IDP-inspired): **FastAPI + LangGraph** backend, **Next.js** frontend (Vercel-friendly), **PostgreSQL**, **FAISS** embeddings.

## Layout

| Path | Role |
|------|------|
| `api/` | Python app (`app` package), `requirements.txt`, `Dockerfile`, scripts |
| `web/` | Next.js 14 (App Router) UI |
| `docker-compose.yml` | Postgres + API (build from repo root: `api/Dockerfile`) |

## Quick start (local)

1. **Postgres** (from repo root):

   ```bash
   docker compose up -d postgres
   ```

2. **API** (from `api/`):

   ```bash
   cd api
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp ../.env.example .env   # edit DB + LLM keys
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Web** (from `web/`):

   ```bash
   cd web
   cp .env.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
   npm install
   npm run dev
   ```

Open [http://localhost:3000](http://localhost:3000) (UI) and [http://localhost:8000/docs](http://localhost:8000/docs) (OpenAPI).

## API

- Versioned routes: `POST /api/v1/chat/insights`, `GET /api/v1/analytics/summary`, etc.
- Legacy: `POST /chat/insights` (same payload as v1).
- **CORS:** set `CORS_ORIGINS` (comma-separated, or `*` for dev). Example: `http://localhost:3000`.

## Deployment sketch

- **Frontend:** Vercel project root = `web/`, env `NEXT_PUBLIC_API_URL` = your API origin.
- **Backend:** any container host (Railway, Fly, etc.); use `api/Dockerfile` with **repository root** as build context (see `docker-compose.prod.yml`).

## Data / embeddings

Default paths under process working directory: `data/raw_docs`, `data/embeddings` (FAISS). Mount a volume in production so indexes persist.
