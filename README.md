# ABEM – Apartment & Building Expense Management

Multi-tenant financial management platform for managing buildings, apartments, shared expenses, and payments.

---

## Architecture

| Layer | Technology |
|---|---|
| Backend API | Django 4.x + DRF + PostgreSQL |
| Web Frontend | React.js + Material UI (Vite) |
| Mobile App | Flutter (Android & iOS) |
| Task Queue | Celery + Redis |
| File Storage | Cloudinary |
| Auth | JWT (djangorestframework-simplejwt) |
| Push Notifications | Firebase FCM |
| CI/CD | GitHub Actions |

---

## Project Structure

```
ABEM/
├── backend/          # Django REST API
│   ├── apps/
│   │   ├── authentication/
│   │   ├── buildings/
│   │   ├── apartments/
│   │   ├── expenses/
│   │   ├── payments/
│   │   ├── notifications/
│   │   └── audit/
│   ├── config/        # Settings (base / dev / prod), URLs, Celery
│   └── requirements/
├── frontend/          # React.js + MUI web app
│   └── src/
│       ├── api/       # Axios clients per domain
│       ├── contexts/  # Zustand auth store
│       ├── pages/     # Page components per sprint
│       ├── routes/    # Protected route setup
│       └── theme/     # MUI theme
├── mobile/            # Flutter app (BLoC pattern)
│   └── lib/
│       ├── core/      # API client, theme, router
│       └── features/  # auth, buildings, expenses, payments, notifications
├── .github/workflows/ # CI pipelines (backend, frontend, mobile)
├── docker-compose.yml      # Development stack
└── docker-compose.prod.yml # Production stack
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
| Django API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/api/docs/ |
| React Frontend | http://localhost:5173 |
| Django Admin | http://localhost:8000/admin/ |
| Health Check | http://localhost:8000/api/health/ |

### 3. Create superuser
```bash
docker compose exec backend python manage.py createsuperuser
```

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

## Sprint Plan

| Sprint | Focus | Status |
|---|---|---|
| 0 | Setup & Architecture | ✅ Done |
| 1 | Auth & User Management | Pending |
| 2 | Buildings & Apartments | Pending |
| 3 | Expense Management | Pending |
| 4 | Payment Management | Pending |
| 5 | Dashboards (Web) | Pending |
| 6 | Notifications | Pending |
| 7 | Flutter Finalization | Pending |
| 8 | Audit & Exports | Pending |
| 9 | Testing & QA | Pending |
| 10 | Deployment & Launch | Pending |

---

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run lint

# Mobile
cd mobile && flutter test
```

---

## CI/CD

Three GitHub Actions workflows run on push/PR to `main` or `develop`:

- **backend-ci.yml** – flake8, black, pytest (≥70% coverage), Docker build
- **frontend-ci.yml** – ESLint, Vite production build
- **mobile-ci.yml** – dart analyze, flutter test
