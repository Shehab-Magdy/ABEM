#!/usr/bin/env bash
# restart.sh — Restart the backend API and frontend web app.
# Restarts: backend, celery_worker, celery_beat, frontend
# Leaves:   db and redis untouched (no data loss)
set -e

cd "$(dirname "$0")"

echo "Restarting backend and frontend services..."
docker compose restart backend celery_worker celery_beat frontend

echo ""
echo "Services restarted."
echo "  API   → http://localhost:8000"
echo "  App   → http://localhost:5173"
