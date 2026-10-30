# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

عِمارة.كوم (3maracom, formerly ABEM) is a multi-tenant platform: Django/DRF API + React web app (also the installable PWA that serves Android and iOS; the Flutter app was removed on branch `feature/react-pwa`), plus two separate test projects. Each **building is a tenant** (`tenant_id` is the building UUID). Two roles: `admin` (full CRUD within their buildings, incl. co-admins) and `owner` (read-only view of own unit data). Feature inventory is in [docs/FEATURES.md](docs/FEATURES.md); production deploy is in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Commands

### Full stack (Docker)
```bash
cp .env.example .env              # then fill in credentials
docker compose up -d              # db, backend (:8000), frontend (:5173)
docker compose up -d db           # database only, if running backend locally (Docker VM disk can run out on Mac)
./scripts/restart.sh [--test|--test-only] # restart backend/frontend, leave db; optionally run smoke tests
./scripts/test.sh [smoke|api|ui|e2e|db]   # runs the tests/playwright suite (creates its own .venv on first run)
```

### Backend (`backend/`, Python 3.13, settings `config.settings.development`)
```bash
pip install -r requirements/development.txt
python manage.py migrate && python manage.py runserver
pytest                                            # collects tests/<app>/test_*.py; coverage gate in pytest.ini (raise it as coverage grows)
pytest tests/authentication/test_auth.py::TestX::test_y --no-cov   # single test
flake8 backend/ ; black --check backend/ ; isort --check-only backend/   # CI lint gates (run from repo root)
```
Swagger at `/api/docs/`, health check at `/api/health/`. Settings are split `config/settings/{base,development,production}.py`; secrets come from env via `python-decouple` (`DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD` are required, no defaults). Tests need a real PostgreSQL — there is no SQLite fallback.

### Frontend (`frontend/`, Node 22+, Vite)
```bash
npm install && npm run dev      # :5173
npm run lint                    # ESLint (CI gate)
npm run build                   # CI gate
npm run format                  # prettier
```
No frontend unit-test runner is configured.

### Test projects (both are black-box suites against a *running* stack, not unit tests)
- `tests/playwright/` — the active suite (what `scripts/test.sh` runs). Layers: `tests/{api,ui,e2e,db,smoke,load}`; `--strict-markers` is on, so new markers must be registered in `pytest.ini`. Per-feature targets in its `Makefile`; Locust for load. Per-test timeout 30s.
- `tests/selenium-legacy/` — older sprint-organized suite (`tests/sprint_0..10`, markers `sprint_N`, `api`, `web`, `smoke`) with Selenium drivers and typed API wrappers in `api/`. Example: `pytest -m smoke --tb=short -q`.

## Architecture

**Backend** (`backend/apps/*`): one Django app per domain — `authentication` (custom `User` model, `AUTH_USER_MODEL = authentication.User`, email login, JWT via simplejwt with role/tenant claims, lockout, forced password change), `buildings`, `apartments`, `expenses` (split logic + categories), `payments`, `notifications` (in-app inbox + FCM), `audit` (immutable log), `dashboard`, `exports` (CSV/XLSX), `core` (exception handler, pagination, middleware, health). Tenant scoping: use `apps/buildings/scoping.py` — `managed_buildings(user)` filters admin querysets to buildings they administer, and `ensure_manages(user, building)` guards create paths. Every new viewset must scope its queryset this way (admins) or by membership (residents). Also in `payments`: InstaPay `PaymentClaim` (resident reports, admin confirms); new `maintenance` app for resident reports. There is no Celery/Redis: the one scheduled job is `python manage.py generate_recurring_expenses`, run daily by the host scheduler (see docs/DEPLOYMENT.md section 12); the cache is in-process LocMem. Media goes to Cloudinary.

**i18n is bilingual en/ar end to end**: backend `locale/{en,ar}` + `APILanguageMiddleware` + Rosetta; frontend `public/locales/{en,ar}` via i18next with RTL (`stylis-plugin-rtl`). A user's preferred language is stored in the DB and synced across devices. New user-facing strings must be added for both languages in both clients.

**Frontend** (`frontend/src`): `api/` has an Axios client per domain, auth state is a Zustand store in `contexts/`, `routes/` holds role-based protected routes, `pages/<domain>/`, MUI theme in `theme/`, and `tutorial/` for the interactive walkthrough.

**Mobile** is the React PWA in `frontend/` (see the `abem-pwa-mobile` skill); there is no native app.

**Load-bearing tutorial anchors**: the interactive tutorial targets specific DOM ids. Do not rename/remove them without updating `TutorialOverlay.jsx` — the full list is in [docs/TUTORIAL_ANCHORS.md](docs/TUTORIAL_ANCHORS.md).

## Gotchas

- CI (`.github/workflows/`) runs backend lint → pytest → Docker build, frontend lint + build, on pushes/PRs to `main`/`develop` (path-filtered). Backend code must pass black, isort and flake8.
- `.env` is gitignored; `.env.example` is the template. The README contains example superuser credentials — don't copy them elsewhere.
- Production CORS origins are configured via regex in `backend/config/settings/production.py`.

## Agent harness

Goal: review, update, create and test the 3maracom backend, web app, Android/iOS (PWA) experience and SRS using project agents in `.claude/agents/`, skills in `.claude/skills/`, and MCP tools in `.mcp.json`.

**Entry point (hard gate):** for any request to review, update, create, fix or test the web app, backend, Android/iOS experience or SRS/QA documents, invoke the `abem-orchestrator` skill before responding. It answers trivial or off-domain questions directly and routes everything else to the agents.

Secrets: the Postgres MCP reads `ABEM_READONLY_DATABASE_URI` (name kept) from your environment; use a read-only role on the dev database only.

| Date | Change | Target | Reason |
|---|---|---|---|
| 2026-10-29 | Created harness (5 agents, 5 skills, orchestrator, tool registry) | `.claude/`, `.mcp.json` | Review/update/create/test web, PWA mobile and SRS |
| 2026-10-29 | Removed Flutter app and mobile CI; replaced stale settings rules | `mobile/`, `.claude/settings.json` | Mobile is now a React PWA |
| 2026-10-29 | Added PWA icons, nginx PWA cache headers, rebuilt abem-playwright venv (Python 3.13) with axe-playwright-python | `frontend/`, `abem-playwright/` | PWA install readiness and accessibility testing |
