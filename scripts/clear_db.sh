#!/usr/bin/env bash
# clear_db.sh — Wipe all operational data while preserving the superuser.
# Runs clear_db.py inside the running backend Docker container.
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Copying clear_db.py into abem-backend-1..."
docker cp "$REPO_ROOT/backend/clear_db.py" abem-backend-1:/app/clear_db.py

echo "Running..."
docker exec abem-backend-1 python /app/clear_db.py
