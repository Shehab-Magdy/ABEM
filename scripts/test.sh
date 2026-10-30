#!/usr/bin/env bash
# test.sh — Run Playwright tests from the project root.
#
# Usage:
#   ./scripts/test.sh                  Run all tests
#   ./scripts/test.sh smoke            Run smoke tests only
#   ./scripts/test.sh api              Run API tests only
#   ./scripts/test.sh ui               Run UI tests only
#   ./scripts/test.sh e2e              Run E2E tests only
#   ./scripts/test.sh db               Run DB tests only
#   ./scripts/test.sh <any pytest args> Pass custom args to pytest
set -e

cd "$(dirname "$0")/../tests/playwright"

if [ ! -d ".venv" ]; then
  echo "Creating test venv..."
  PY=$(command -v python3.13 || command -v python3)
  "$PY" -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
  .venv/bin/playwright install chromium
fi

ARGS=("$@")

# Map shorthand names to test directories/markers
case "${1:-}" in
  smoke) ARGS=(-m smoke tests/smoke/) ;;
  api)   ARGS=(-m api tests/api/) ;;
  ui)    ARGS=(-m ui tests/ui/) ;;
  e2e)   ARGS=(tests/e2e/) ;;
  db)    ARGS=(tests/db/) ;;
esac

[ ${#ARGS[@]} -eq 0 ] && ARGS=(tests/)

.venv/bin/pytest "${ARGS[@]}" --tb=short -v
