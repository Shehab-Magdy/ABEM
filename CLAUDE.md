# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

ABEM (Apartment & Building Expense Management) is a multi-tenant platform: Django/DRF API + React web app + Flutter mobile app, plus two separate test projects. Each **building is a tenant** (`tenant_id` is the building UUID). Two roles: `admin` (full CRUD within their buildings, incl. co-admins) and `owner` (read-only view of own unit data). Feature inventory is in [FEATURES.md](FEATURES.md); production deploy is in [DEPLOYMENT.md](DEPLOYMENT.md).

## Commands

### Full stack (Docker)
```bash
cp .env.example .env              # then fill in credentials
docker compose up -d              # db, redis, backend (:8000), celery worker/beat, frontend (:5173)
docker compose up -d db redis     # infra only, if running backend locally (Docker VM disk can run out on Mac)
./restart.sh [--test|--test-only] # restart backend/celery/frontend, leave db+redis; optionally run smoke tests
./test.sh [smoke|api|ui|e2e|db]   # runs the abem-playwright suite (creates its own .venv on first run)
```

### Backend (`backend/`, Python 3.13, settings `config.settings.development`)
```bash
pip install -r requirements/development.txt
python manage.py migrate && python manage.py runserver
pytest                                            # enforces --cov-fail-under=70 (set in pytest.ini)
pytest tests/authentication/test_auth.py::TestX::test_y --no-cov   # single test
flake8 backend/ ; black --check backend/ ; isort --check-only backend/   # CI lint gates (run from repo root)
```
Swagger at `/api/docs/`, health check at `/api/health/`. Settings are split `config/settings/{base,development,production}.py`; secrets come from env via `python-decouple` (`DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD` are required, no defaults). Tests need a real PostgreSQL (and Redis) — there is no SQLite fallback.

### Frontend (`frontend/`, Node 22+, Vite)
```bash
npm install && npm run dev      # :5173
npm run lint                    # ESLint (CI gate)
npm run build                   # CI gate
npm run format                  # prettier
```
No frontend unit-test runner is configured.

### Mobile (`mobile/`)
```bash
flutter pub get && flutter test && dart analyze
```

### Test projects (both are black-box suites against a *running* stack, not unit tests)
- `abem-playwright/` — the active suite (what `test.sh` runs). Layers: `tests/{api,ui,e2e,db,smoke,load}`; `--strict-markers` is on, so new markers must be registered in `pytest.ini`. Per-feature targets in its `Makefile`; Locust for load. Per-test timeout 30s.
- `abem-automation/` — older sprint-organized suite (`tests/sprint_0..10`, markers `sprint_N`, `api`, `web`, `mobile`, `smoke`) with Selenium/Appium drivers and typed API wrappers in `api/`. Example: `pytest -m smoke --tb=short -q`.

## Architecture

**Backend** (`backend/apps/*`): one Django app per domain — `authentication` (custom `User` model, `AUTH_USER_MODEL = authentication.User`, email login, JWT via simplejwt with role/tenant claims, lockout, forced password change), `buildings`, `apartments`, `expenses` (split logic + categories), `payments`, `notifications` (in-app inbox + FCM), `audit` (immutable log), `dashboard`, `exports` (CSV/XLSX), `core` (exception handler, pagination, middleware, health). Cross-cutting tenant scoping lives in the `mixins.py` / `permissions.py` modules inside the apps — read these before adding a viewset, since list querysets must be scoped to the requesting user's buildings (admins also see users they `created_by`). Celery (`config/celery.py`, Redis broker, django-celery-beat) handles async work. Media goes to Cloudinary.

**i18n is bilingual en/ar end to end**: backend `locale/{en,ar}` + `APILanguageMiddleware` + Rosetta; frontend `public/locales/{en,ar}` via i18next with RTL (`stylis-plugin-rtl`); mobile has its own. A user's preferred language is stored in the DB and synced across devices. New user-facing strings must be added for both languages in all three clients.

**Frontend** (`frontend/src`): `api/` has an Axios client per domain, auth state is a Zustand store in `contexts/`, `routes/` holds role-based protected routes, `pages/<domain>/`, MUI theme in `theme/`, and `tutorial/` for the interactive walkthrough.

**Mobile** (`mobile/lib`): Flutter with BLoC; `features/<domain>/` mirrors the backend domains, `core/` has API client/theme/router, `tutorial/` has the walkthrough overlay.

**Load-bearing tutorial anchors**: the interactive tutorial targets specific DOM ids (React) and `GlobalKey`s (Flutter). Do not rename/remove them without updating `TutorialOverlay.jsx` and `walkthrough_overlay.dart` — the full list is in [TUTORIAL_ANCHORS.md](TUTORIAL_ANCHORS.md).

## Gotchas

- CI (`.github/workflows/`) runs backend lint → pytest → Docker build, frontend lint + build, and mobile analyze + test, on pushes/PRs to `main`/`develop` (path-filtered). Backend code must pass black, isort and flake8.
- `.env` is gitignored; `.env.example` is the template. The README contains example superuser credentials — don't copy them elsewhere.
- Production CORS origins are configured via regex in `backend/config/settings/production.py`.
