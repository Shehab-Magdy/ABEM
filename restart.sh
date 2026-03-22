#!/usr/bin/env bash
# restart.sh — Restart the backend API and frontend web app.
# Restarts: backend, celery_worker, celery_beat, frontend
# Leaves:   db and redis untouched (no data loss)
#
# Usage:
#   ./restart.sh            Restart services only
#   ./restart.sh --test     Restart then run smoke tests
#   ./restart.sh --test-only  Run smoke tests without restarting
#
# Environment:
#   APP_HOST  Override the host used for health checks and tests
#             (default: auto-detect from .env or fall back to 127.0.0.1)
set -e

cd "$(dirname "$0")"

# ── Resolve host ──────────────────────────────────────────────
if [ -z "$APP_HOST" ] && [ -f .env ]; then
  APP_HOST=$(grep -E '^APP_HOST=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]')
fi
APP_HOST="${APP_HOST:-127.0.0.1}"

API_URL="http://${APP_HOST}:8000"
APP_URL="http://${APP_HOST}:5173"

RUN_TESTS=false
SKIP_RESTART=false

for arg in "$@"; do
  case "$arg" in
    --test)       RUN_TESTS=true ;;
    --test-only)  RUN_TESTS=true; SKIP_RESTART=true ;;
    -h|--help)
      echo "Usage: ./restart.sh [--test] [--test-only]"
      echo "  --test        Restart services, then run smoke tests"
      echo "  --test-only   Run smoke tests without restarting"
      echo ""
      echo "Environment:"
      echo "  APP_HOST=<ip>  Override host (current: ${APP_HOST})"
      exit 0 ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

# ── Restart services ──────────────────────────────────────────
if [ "$SKIP_RESTART" = false ]; then
  echo "Restarting backend and frontend services..."
  docker compose restart backend celery_worker celery_beat frontend

  # Wait for backend to be healthy
  echo ""
  echo "Waiting for backend health check (${API_URL})..."
  retries=0
  max_retries=30
  until curl -sf "${API_URL}/api/v1/health/" > /dev/null 2>&1 \
     || curl -sf "${API_URL}/api/v1/auth/login/" > /dev/null 2>&1; do
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
fi

# ── Run smoke tests ───────────────────────────────────────────
if [ "$RUN_TESTS" = true ]; then
  echo ""
  echo "Running smoke tests..."

  if [ -d "abem-playwright" ]; then
    cd abem-playwright
    if [ ! -d ".venv" ]; then
      echo "  Creating test venv..."
      python3 -m venv .venv
      .venv/bin/pip install -q -r requirements.txt
      .venv/bin/playwright install chromium
    fi

    # Pass resolved host to the test framework
    BASE_URL="${APP_URL}" \
    API_BASE_URL="${API_URL}" \
    DB_HOST="${APP_HOST}" \
    .venv/bin/pytest tests/smoke/ -m smoke --tb=short 2>&1
    exit_code=$?
    cd ..

    echo ""
    if [ "$exit_code" -eq 0 ]; then
      echo "Smoke tests passed."
    else
      echo "Smoke tests FAILED (exit code $exit_code)."
      echo "  Full report: abem-playwright/reports/test_report.html"
      exit "$exit_code"
    fi
  else
    echo "  abem-playwright/ directory not found — skipping tests."
  fi
fi
