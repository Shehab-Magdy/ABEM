# ABEM – Apartment & Building Expense Management

Multi-tenant financial management platform for managing buildings, apartments, shared expenses, and payments.

---

## Architecture

| Layer | Technology |
|---|---|
| Backend API | Django 4.2 + DRF + PostgreSQL 16 |
| Web Frontend | React.js + Material UI (Vite) |
| Mobile App | Flutter 3.x (Android & iOS) |
| Task Queue | Celery + Redis 7 |
| File Storage | Cloudinary |
| Auth | JWT (djangorestframework-simplejwt) |
| Push Notifications | Firebase FCM |
| API Docs | drf-spectacular (OpenAPI 3 / Swagger) |
| CI/CD | GitHub Actions |

---

## Project Structure

```
ABEM/
├── backend/                    # Django REST API
│   ├── apps/
│   │   ├── authentication/     # JWT auth, users, roles
│   │   ├── buildings/          # Building & user assignment
│   │   ├── apartments/         # Apartment CRUD
│   │   ├── expenses/           # Shared expenses & split logic
│   │   ├── payments/           # Payment recording & receipts
│   │   ├── dashboard/          # Admin & owner dashboards
│   │   ├── notifications/      # In-app notification inbox
│   │   ├── audit/              # Immutable audit log
│   │   ├── exports/            # CSV/XLSX data exports
│   │   └── core/               # Health check, exception handler
│   ├── config/                 # Settings (base / dev / prod), URLs, Celery
│   └── requirements/           # base.txt / development.txt / production.txt
├── frontend/                   # React.js + MUI web app
│   └── src/
│       ├── api/                # Axios clients per domain
│       ├── contexts/           # Zustand auth store
│       ├── pages/              # Page components per sprint
│       ├── routes/             # Protected route setup
│       └── theme/              # MUI theme
├── mobile/                     # Flutter app (BLoC pattern)
│   └── lib/
│       ├── core/               # API client, theme, router
│       └── features/           # auth, buildings, expenses, payments, notifications
├── abem-automation/            # Pytest automation suite (480+ tests)
│   ├── tests/                  # Sprint-based test folders (sprint_0 – sprint_10)
│   ├── api/                    # Typed API wrappers
│   ├── core/                   # APIClient, WebDriver, MobileDriver
│   └── utils/                  # Test data factories, logger
├── .github/workflows/          # CI pipelines (backend, frontend, mobile)
├── DEPLOYMENT.md               # Step-by-step production deployment guide
├── docker-compose.yml          # Development stack
└── docker-compose.prod.yml     # Production stack
```

---

## Quick Start (Development)

### Prerequisites
- Docker & Docker Compose
- Node 22+ (for local frontend dev without Docker)
- Python 3.13+ (for local backend dev without Docker)

### 1. Configure environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start all services
```bash
docker compose up -d
```

| Service | URL |
|---|---|
| Django API | http://localhost:8000/api/v1/ |
| API Docs (Swagger) | http://localhost:8000/api/docs/ |
| API Docs (ReDoc) | http://localhost:8000/api/redoc/ |
| React Frontend | http://localhost:5173 |
| Django Admin | http://localhost:8000/admin/ |
| Health Check | http://localhost:8000/api/health/ |

### 3. Create superuser
```bash
docker compose exec backend python manage.py createsuperuser
```

| Field | Value |
|---|---|
| Username | `shebo` |
| Email | `cegres1@yahoo.com` |
| Password | `L7r@xval8` |

### 4. Local backend (without Docker)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/development.txt
python manage.py migrate
python manage.py runserver
```

### 5. Local frontend (without Docker)
```bash
cd frontend
npm install
npm run dev
```

---

## API Documentation (Swagger)

The API is fully documented via **OpenAPI 3** using [drf-spectacular](https://drf-spectacular.readthedocs.io/).

| Endpoint | Description |
|---|---|
| `GET /api/docs/` | Interactive Swagger UI |
| `GET /api/redoc/` | ReDoc documentation |
| `GET /api/schema/` | Raw OpenAPI YAML/JSON schema |

All endpoints require **Bearer JWT** authentication (except `/auth/login/` and `/auth/register/`).

---

## Sprint Plan

| Sprint | Focus | Tests | Status |
|---|---|---|---|
| 0 | Setup & Architecture | 20 | ✅ Done |
| 1 | Auth & User Management | 55 | ✅ Done |
| 2 | Buildings & Apartments | 55 | ✅ Done |
| 3 | Expense Management | 65 | ✅ Done |
| 4 | Payment Management | 70 | ✅ Done |
| 5 | Dashboards (Web) | 40 | ✅ Done |
| 6 | Notifications | 50 | ✅ Done |
| 7 | Flutter Finalization | 35 | ✅ Done |
| 8 | Audit & Exports | 40 | ✅ Done |
| 9 | Performance & Security | 35 | ✅ Done |
| 10 | Deployment & Launch | 15 | ✅ Done |
| **Total** | | **480+** | ✅ **Complete** |

---

## Testing

### Run Automation Suite

```bash
cd abem-automation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

```bash
# All tests
pytest

# By sprint
pytest -m sprint_10

# Smoke tests only (post-deployment gate — 15 tests, < 60 seconds)
pytest -m smoke --tb=short -q

# API tests only
pytest -m api

# Full regression run (all 480+ tests)
pytest --tb=short -q
```

### By Layer

```bash
# Backend unit tests
cd backend && pytest

# Frontend linting
cd frontend && npm run lint

# Mobile tests
cd mobile && flutter test
```

---

## CI/CD

Three GitHub Actions workflows run on push/PR to `main` or `develop`:

| Workflow | Checks |
|---|---|
| `backend-ci.yml` | flake8, black, pytest (≥70% coverage), Docker build |
| `frontend-ci.yml` | ESLint, Vite production build |
| `mobile-ci.yml` | dart analyze, flutter test |

---

## Production Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the complete step-by-step production deployment guide, covering:

- Server provisioning & firewall setup
- Docker production deployment
- Database setup & migrations
- Nginx + Let's Encrypt TLS configuration
- Celery worker configuration
- Mobile app release (Play Store / App Store)
- Monitoring with Sentry
- Rollback procedure
- Security hardening checklist

---

## Key Endpoints (Quick Reference)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login/` | Login → returns JWT access + refresh |
| `POST` | `/api/v1/auth/refresh/` | Refresh access token |
| `GET` | `/api/v1/buildings/` | List buildings |
| `GET` | `/api/v1/apartments/` | List apartments |
| `GET` | `/api/v1/expenses/` | List expenses |
| `GET` | `/api/v1/payments/` | List payments |
| `GET` | `/api/v1/dashboard/admin/` | Admin financial dashboard |
| `GET` | `/api/v1/notifications/` | Notification inbox |
| `GET` | `/api/v1/audit/` | Audit log (admin only) |
| `GET` | `/api/v1/exports/payments/?file_format=csv` | Export payments (CSV/XLSX) |
| `GET` | `/api/health/` | Health check |
| `GET` | `/api/docs/` | Swagger UI |
