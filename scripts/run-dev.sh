#!/usr/bin/env bash
# DocSage local dev: Postgres (Docker) + FastAPI + Next.js — one command.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
  echo "Usage: $0 [--no-docker]"
  echo "  Starts Postgres via docker compose (unless --no-docker), then API + web."
  echo "  Env: API_PORT (default $API_PORT), WEB_PORT (default $WEB_PORT)."
  exit 0
fi

NO_DOCKER=false
[[ "${1:-}" == "--no-docker" ]] && NO_DOCKER=true

if [[ "$NO_DOCKER" == false ]] && command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    docker compose up -d postgres
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose up -d postgres
  fi
elif [[ "$NO_DOCKER" == false ]]; then
  echo "Warning: docker not found; ensure Postgres is running (or use SQLite: set USE_SQLITE in api/.env)." >&2
fi

[[ -f api/.env ]] || cp .env.example api/.env
[[ -f web/.env.local ]] || echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:${API_PORT}" > web/.env.local

VENV="$ROOT/api/.venv"
PIP="$VENV/bin/pip"
UVICORN="$VENV/bin/uvicorn"
if [[ ! -x "$VENV/bin/python" ]]; then
  python3 -m venv "$VENV"
fi
"$PIP" install -q -r "$ROOT/api/requirements.txt"

[[ -d web/node_modules ]] || (cd web && npm install)

cleanup() {
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "${WEB_PID:-}" ]] && kill "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "API  → http://127.0.0.1:${API_PORT}/docs"
echo "Web  → http://127.0.0.1:${WEB_PORT}"
echo "Ctrl+C stops API + web (Postgres keeps running)."
echo ""

(
  cd "$ROOT/api"
  exec "$UVICORN" app.main:app --reload --host 0.0.0.0 --port "$API_PORT"
) &
API_PID=$!

(
  cd "$ROOT/web"
  exec npm run dev -- -p "$WEB_PORT"
) &
WEB_PID=$!

wait
