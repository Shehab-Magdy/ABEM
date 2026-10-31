#!/usr/bin/env bash
# seed_data.sh — Fill the dev database with sample users, buildings, units, expenses and payments.
# Runs backend `manage.py seed_demo_data` in the running backend compose service. Safe to re-run.
#
# Usage:
#   ./scripts/seed_data.sh                    Seed (skips buildings that already have units)
#   ./scripts/seed_data.sh --reset            Delete the previously seeded data, then seed again
#   ./scripts/seed_data.sh --password 'X@1'   Use another password for all seeded users
#
# Logins (default password P@ssw0rd): cegres1@hotmail.com (superuser), admin@abem.test,
# admin2@abem.test, owner@abem.test, owner2..owner6@abem.test
set -e

cd "$(dirname "$0")/.."

docker compose exec -T backend python manage.py seed_demo_data "$@"
