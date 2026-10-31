#!/usr/bin/env bash
# restart.sh — Start or restart the backend API and frontend web app.
# Starts:   backend, frontend (creates them if missing, restarts them if running)
# Leaves:   db data untouched (the db container is started if it is stopped)
#
# Usage:
#   ./scripts/restart.sh                 Localhost only (127.0.0.1)
#   ./scripts/restart.sh --lan           Serve on this machine's LAN IP so other
#                                        devices (phone, tablet) can open the app
#   ./scripts/restart.sh --host <ip>     Serve on a specific IP / hostname
#   ./scripts/restart.sh --test          Restart then run smoke tests
#   ./scripts/restart.sh --test-only     Run smoke tests without restarting
#
# Environment:
#   APP_HOST  Host used for URLs, CORS/ALLOWED_HOSTS and tests
#             (default: APP_HOST from .env, else 127.0.0.1)
set -e

cd "$(dirname "$0")/.."

detect_lan_ip() {
  local ip=""
  if [ "$(uname)" = "Darwin" ]; then
    for iface in en0 en1 en2 en3; do
      ip=$(ipconfig getifaddr "$iface" 2>/dev/null || true)
      [ -n "$ip" ] && break
    done
  else
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
  fi
  echo "$ip"
}

# ── Resolve host ──────────────────────────────────────────────
if [ -z "$APP_HOST" ] && [ -f .env ]; then
  APP_HOST=$(grep -E '^APP_HOST=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]')
fi
APP_HOST="${APP_HOST:-127.0.0.1}"

RUN_TESTS=false
SKIP_RESTART=false

while [ $# -gt 0 ]; do
  arg="$1"; shift
  case "$arg" in
    --lan)
      APP_HOST=$(detect_lan_ip)
      if [ -z "$APP_HOST" ]; then
        echo "Could not detect a LAN IP. Connect to Wi-Fi/Ethernet or use --host <ip>."
        exit 1
      fi ;;
    --host)
      APP_HOST="${1:?--host needs an IP or hostname}"; shift ;;
    --test)       RUN_TESTS=true ;;
    --test-only)  RUN_TESTS=true; SKIP_RESTART=true ;;
    -h|--help)
      echo "Usage: ./scripts/restart.sh [--lan | --host <ip>] [--test] [--test-only]"
      echo "  --lan         Serve on this machine's LAN IP (open from phone/other devices)"
      echo "  --host <ip>   Serve on a specific IP or hostname"
      echo "  --test        Restart services, then run smoke tests"
      echo "  --test-only   Run smoke tests without restarting"
      echo ""
      echo "Environment:"
      echo "  APP_HOST=<ip>  Override host (current: ${APP_HOST})"
      exit 0 ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

API_URL="http://${APP_HOST}:8000"
APP_URL="http://${APP_HOST}:5173"

# Passed through to docker-compose.yml: the browser calls the API on this host,
# and Django must accept requests addressed to it.
export VITE_API_BASE_URL="${API_URL}/api/v1"
export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1,${APP_HOST}"

# ── Restart services ──────────────────────────────────────────
if [ "$SKIP_RESTART" = false ]; then
  # `up -d` creates missing containers and recreates ones whose env changed
  # (e.g. a new --lan IP); containers that were already up and unchanged are
  # then restarted to pick up code/config changes.
  was_running=$(docker compose ps --status running -q backend frontend 2>/dev/null | wc -l | tr -d ' ')
  echo "Starting backend and frontend services on ${APP_HOST}..."
  docker compose up -d backend frontend
  if [ "$was_running" -gt 0 ]; then
    docker compose restart backend frontend
  fi

  # Wait for backend to be healthy
  echo ""
  echo "Waiting for backend health check (${API_URL})..."
  retries=0
  max_retries=180  # first start runs migrate / npm install
  until curl -sf "${API_URL}/api/health/" > /dev/null 2>&1; do
    retries=$((retries + 1))
    if [ "$retries" -ge "$max_retries" ]; then
      echo "  Backend did not become healthy after ${max_retries}s"
      echo "  Check logs: docker compose logs backend --tail 50"
      exit 1
    fi
    sleep 1
  done
  echo "  Backend is up."

  # Wait for frontend to be healthy
  retries=0
  until curl -sf "${APP_URL}/" > /dev/null 2>&1; do
    retries=$((retries + 1))
    if [ "$retries" -ge "$max_retries" ]; then
      echo "  Frontend did not become healthy after ${max_retries}s"
      echo "  Check logs: docker compose logs frontend --tail 50"
      exit 1
    fi
    sleep 1
  done
  echo "  Frontend is up."

  echo ""
  echo "Services restarted."
  echo "  API   → ${API_URL}"
  echo "  App   → ${APP_URL}"
  if [ "$APP_HOST" != "127.0.0.1" ] && [ "$APP_HOST" != "localhost" ]; then
    echo ""
    echo "Open ${APP_URL} from any device on the same network."
    echo "  If it does not load, allow ports 5173 and 8000 in the macOS firewall."
    echo "  Note: the PWA install prompt and service worker need HTTPS off localhost,"
    echo "  so on a phone the app runs as a normal web page over http."
  fi
fi

# ── Run smoke tests ───────────────────────────────────────────
if [ "$RUN_TESTS" = true ]; then
  echo ""
  echo "Running smoke tests..."

  if [ -d "tests/playwright" ]; then
    cd tests/playwright
    if [ ! -d ".venv" ]; then
      echo "  Creating test venv..."
      PY=$(command -v python3.13 || command -v python3)
      "$PY" -m venv .venv
      .venv/bin/pip install -q -r requirements.txt
      .venv/bin/playwright install chromium
    fi

    # Pass resolved host to the test framework
    BASE_URL="${APP_URL}" \
    API_BASE_URL="${API_URL}" \
    DB_HOST="${APP_HOST}" \
    .venv/bin/pytest tests/smoke/ -m smoke --tb=short 2>&1 || exit_code=$?
    exit_code="${exit_code:-0}"
    cd ../..

    echo ""
    if [ "$exit_code" -eq 0 ]; then
      echo "Smoke tests passed."
    else
      echo "Smoke tests FAILED (exit code $exit_code)."
      echo "  Full report: tests/playwright/reports/test_report.html"
      exit "$exit_code"
    fi
  else
    echo "  tests/playwright/ directory not found — skipping tests."
  fi
fi
