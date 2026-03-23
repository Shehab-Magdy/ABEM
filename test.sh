#!/usr/bin/env bash
# test.sh — Run Playwright tests from the project root.
#
# Usage:
#   ./test.sh                  Run all tests
#   ./test.sh smoke            Run smoke tests only
#   ./test.sh api              Run API tests only
#   ./test.sh ui               Run UI tests only
#   ./test.sh e2e              Run E2E tests only
#   ./test.sh db               Run DB tests only
#   ./test.sh <any pytest args> Pass custom args to pytest
set -e

cd "$(dirname "$0")/abem-playwright"

if [ ! -d ".venv" ]; then
  echo "Creating test venv..."
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
  .venv/bin/playwright install chromium
fi

ARGS="$@"

# Map shorthand names to test directories/markers
case "${1:-}" in
  smoke) ARGS="-m smoke tests/smoke/" ;;
  api)   ARGS="-m api tests/api/" ;;
  ui)    ARGS="-m ui tests/ui/" ;;
  e2e)   ARGS="tests/e2e/" ;;
  db)    ARGS="tests/db/" ;;
esac

.venv/bin/pytest ${ARGS:- tests/} --tb=short -v
