#!/usr/bin/env bash
# DocSage local dev: Postgres (Docker) + FastAPI + Next.js — one command.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_COMPOSE="${ROOT}/docker-compose.postgres.yml"

if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
  echo "Usage: $0 [--no-docker]"
  echo "  Starts Postgres via Docker (unless --no-docker), then API + web."
  echo "  If Docker is not running, Postgres is skipped; use SQLite (USE_SQLITE=true in api/.env) or start Docker Desktop."
  echo "  Env: API_PORT (default $API_PORT), WEB_PORT (default $WEB_PORT), POSTGRES_PORT (default $POSTGRES_PORT)."
  echo "  web/.env.local NEXT_PUBLIC_API_URL is updated to http://127.0.0.1:\$API_PORT each run (restart Next after URL changes)."
  echo "  If 5432 is already in use: POSTGRES_PORT=5433 $0 and set POSTGRES_PORT=5433 in api/.env."
  exit 0
fi

NO_DOCKER=false
[[ "${1:-}" == "--no-docker" ]] && NO_DOCKER=true

# Sync web/.env.local NEXT_PUBLIC_API_URL with API_PORT (Next reads it when the dev server starts).
upsert_web_api_url() {
  python3 - "$ROOT" "$API_PORT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
port = sys.argv[2]
url = f"http://127.0.0.1:{port}"
path = root / "web" / ".env.local"
lines = path.read_text().splitlines() if path.exists() else []
out: list[str] = []
seen = False
for line in lines:
    if line.startswith("NEXT_PUBLIC_API_URL="):
        if not seen:
            out.append(f"NEXT_PUBLIC_API_URL={url}")
            seen = True
    else:
        out.append(line)
if not seen:
    out.append(f"NEXT_PUBLIC_API_URL={url}")
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
}

start_postgres_container() {
  if [[ "$NO_DOCKER" == true ]]; then
    echo "Skipping Postgres container (--no-docker)." >&2
    return 0
  fi
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker not installed; skipping Postgres. Use USE_SQLITE=true in api/.env or install Docker for Postgres." >&2
    return 0
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon not running; skipping Postgres container. Start Docker Desktop, or set USE_SQLITE=true in api/.env for a local DB without Docker." >&2
    return 0
  fi
  if [[ ! -f "$POSTGRES_COMPOSE" ]]; then
    echo "Missing $POSTGRES_COMPOSE" >&2
    return 1
  fi
  if docker compose version >/dev/null 2>&1; then
    if ! docker compose -f "$POSTGRES_COMPOSE" up -d postgres; then
      echo "Postgres container did not start. If the host port is busy, try:" >&2
      echo "  POSTGRES_PORT=5433 $0   # and set POSTGRES_PORT=5433 in api/.env" >&2
    fi
  elif command -v docker-compose >/dev/null 2>&1; then
    if ! docker-compose -f "$POSTGRES_COMPOSE" up -d postgres; then
      echo "Postgres container did not start. If the host port is busy, try:" >&2
      echo "  POSTGRES_PORT=5433 $0   # and set POSTGRES_PORT=5433 in api/.env" >&2
    fi
  else
    echo "docker compose not available; skipping Postgres." >&2
    return 0
  fi
}

start_postgres_container || true

[[ -f api/.env ]] || cp .env.example api/.env
upsert_web_api_url

VENV="$ROOT/api/.venv"
PIP="$VENV/bin/pip"
UVICORN="$VENV/bin/uvicorn"

venv_broken() {
  [[ ! -x "$VENV/bin/python" ]] && return 0
  if ! "$VENV/bin/python" -c "import sys" >/dev/null 2>&1; then
    return 0
  fi
  [[ ! -x "$PIP" ]] && return 0
  if ! "$PIP" --version >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

if venv_broken; then
  echo "Recreating api/.venv (missing, copied from elsewhere, or broken interpreter) ..." >&2
  rm -rf "$VENV"
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
echo "Web points at NEXT_PUBLIC_API_URL from web/.env.local (updated to http://127.0.0.1:${API_PORT} by this script)."
echo "If login/register cannot reach the API: ensure API started, curl http://127.0.0.1:${API_PORT}/health, and open the app at http://127.0.0.1:${WEB_PORT} (or add that origin to CORS_ORIGINS in api/.env)."
echo "Ctrl+C stops API + web (Postgres container keeps running if started)."
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
