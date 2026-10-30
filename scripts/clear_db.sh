#!/usr/bin/env bash
# clear_db.sh — Wipe all operational data while preserving the superuser.
# Runs backend/clear_db.py inside the running backend compose service.
# Dev database only: this deletes every building, unit, expense, payment and non-superuser account.
set -e

cd "$(dirname "$0")/.."

if [ "${1:-}" != "--yes" ]; then
  read -r -p "This wipes all operational data in the dev database. Continue? [y/N] " answer
  case "$answer" in [yY]*) ;; *) echo "Aborted."; exit 1 ;; esac
fi

echo "Running clear_db.py in the backend service..."
docker compose exec -T backend python clear_db.py
