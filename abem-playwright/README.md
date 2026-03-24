# ABEM Playwright Test Framework

Professional test automation framework for the ABEM (Apartment & Building Expense Management) system using Playwright, pytest, Locust, and psycopg2.

## Prerequisites

- Python 3.12+
- Node.js (for the frontend dev server)
- PostgreSQL running with the ABEM database
- Backend server running at `http://localhost:8000`
- Frontend dev server running at `http://localhost:5173`

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Copy and configure environment
cp .env.example .env
# Edit .env with your actual credentials and URLs

# 4. Verify services are running
curl -s http://localhost:5173/login | head -1   # Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/auth/login/  # Backend (expect 405)
```

## Running Tests

### UI Tests (Playwright)

```bash
# Run all UI tests
pytest tests/ui/ -v

# Run with HTML report
pytest tests/ui/ -v --html=reports/ui_report.html --self-contained-html

# Run in parallel (faster)
pytest tests/ui/ -v -n auto --html=reports/ui_report.html --self-contained-html

# Run by sprint
pytest tests/ui/ -v -m sprint1          # Auth & User Management
pytest tests/ui/ -v -m sprint2          # Buildings & Apartments
pytest tests/ui/ -v -m sprint3          # Expense Management
pytest tests/ui/ -v -m sprint4          # Payment Management
pytest tests/ui/ -v -m sprint5          # Dashboards
pytest tests/ui/ -v -m sprint6          # Notifications
pytest tests/ui/ -v -m sprint8          # Audit & Exports

# Run by category
pytest tests/ui/ -v -m auth            # Authentication tests
pytest tests/ui/ -v -m financial        # Financial P0 tests (rounding, credit)
pytest tests/ui/ -v -m rbac            # Role-based access control
pytest tests/ui/ -v -m performance      # Page load timing

# Run a specific test file
pytest tests/ui/auth/test_login_ui.py -v
pytest tests/ui/expenses/test_expense_management.py -v
pytest tests/ui/payments/test_payment_management.py -v
```

### API Tests

```bash
pytest tests/api/ -v -m api
```

### E2E Tests

```bash
pytest tests/e2e/ -v -m e2e
```

### Smoke Tests

```bash
pytest tests/smoke/ -v -m smoke
```

### Database Tests

```bash
pytest tests/db/ -v -m db
```

### Full Regression (all test types)

```bash
pytest -v -n auto --html=reports/regression_report.html --self-contained-html
```

### Load & Stress Tests (Locust)

```bash
# Smoke load test — 10 users, 30 seconds
cd tests/load
locust -f scenarios/smoke_load.py --headless -u 10 -r 2 --run-time 30s \
  --host http://localhost:8000

# Normal load test — 100 users, 5 minutes
locust -f scenarios/normal_load.py --headless -u 100 -r 10 --run-time 5m \
  --host http://localhost:8000 --html ../../reports/normal_load.html

# Stress test — ramp from 50 to 300 users over 10 minutes
locust -f scenarios/stress_test.py --headless \
  --host http://localhost:8000 --html ../../reports/stress_test.html

# Interactive mode (opens web UI at http://localhost:8089)
locust -f locustfile.py --host http://localhost:8000
```

### Using the Makefile

```bash
make install            # Install deps + Chromium
make test-auth          # Sprint 1 auth tests
make test-expenses      # Sprint 3 expense tests
make test-payments      # Sprint 4 payment tests
make test-dashboards    # Sprint 5 dashboard tests
make test-financial     # All financial P0 tests
make test-rbac          # All RBAC tests
make test-ui-all        # All UI tests (sequential)
make test-ui-parallel   # All UI tests (parallel)
make load-smoke         # 10-user smoke load test
make load-normal        # 100-user normal load test
make load-stress        # 50-300 user stress ramp
make test-all           # Full regression + smoke load
```

## Directory Structure

```
abem-playwright/
├── conftest.py             # Global fixtures, browser setup, auth helpers
├── pytest.ini              # Markers, timeout, reporting config
├── requirements.txt        # Pinned dependencies
├── .env.example            # All required env vars documented
├── Makefile                # Convenience run targets
├── pw_config.py            # Browser and viewport configuration
│
├── pages/                  # Page Object Model classes
│   ├── base_page.py        # Shared navigation, wait, toast helpers
│   ├── login_page.py       # Login form interactions
│   ├── dashboard_page.py   # Dashboard KPI cards, filters, charts
│   ├── buildings_page.py   # Building CRUD, unit management
│   ├── expenses_page.py    # Expense form, split breakdown, filters
│   ├── payments_page.py    # Payment recording, balance display
│   ├── notifications_page.py
│   ├── users_page.py
│   ├── profile_page.py
│   ├── categories_page.py
│   ├── exports_page.py
│   └── audit_page.py
│
├── tests/
│   ├── api/                # API-layer tests (no browser)
│   ├── ui/                 # Playwright UI tests
│   │   ├── auth/           # Login, logout, RBAC
│   │   ├── buildings/      # Building & apartment management
│   │   ├── expenses/       # Expense CRUD, split rounding
│   │   ├── payments/       # Payment recording, credit balance
│   │   ├── dashboard/      # Dashboard cards, charts, filters
│   │   ├── notifications/  # Notification bell, broadcast
│   │   ├── exports/        # Audit log, CSV/XLSX export
│   │   ├── performance/    # Page load timing assertions
│   │   └── accessibility/  # Keyboard nav, alt text, labels
│   ├── e2e/                # Full user journey tests
│   ├── db/                 # Database integrity tests
│   ├── smoke/              # Quick health-check suite
│   └── load/               # Locust load & stress tests
│       ├── locustfile.py   # AdminUser + OwnerUser with JWT refresh
│       ├── tasks/          # Reusable task modules
│       └── scenarios/      # smoke (10u), normal (100u), stress (300u)
│
├── fixtures/               # Shared pytest fixtures (auth, buildings, etc.)
├── utils/                  # API client, data factory, assertions, DB client
└── config/                 # Environment settings loader
```

## Test Reports

After running tests, reports are generated in `reports/`:

- `reports/ui_report.html` — Playwright UI test results
- `reports/test_report.html` — Default pytest HTML report
- `reports/test_run.log` — Debug-level execution log

Open any HTML report in a browser:
```bash
open reports/ui_report.html   # macOS
xdg-open reports/ui_report.html  # Linux
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BASE_URL` | Frontend URL | `http://localhost:5173` |
| `API_BASE_URL` | Backend API URL | `http://localhost:8000` |
| `ADMIN_EMAIL` | Admin test account | `admin@abem.test` |
| `ADMIN_PASSWORD` | Admin password | — |
| `OWNER_EMAIL` | Owner test account | `owner@abem.test` |
| `OWNER_PASSWORD` | Owner password | — |
| `HEADLESS` | Run browser headless | `true` |
| `SLOW_MO` | Slow down actions (ms) | `0` |
| `BROWSER` | Browser engine | `chromium` |
| `LOCUST_HOST` | Load test target URL | `http://localhost:8000` |

## Technology Stack

| Layer | Tool |
|-------|------|
| Test runner | pytest >=8.1 |
| Browser | Playwright (Python) >=1.44 |
| Load testing | Locust >=2.29 |
| API client | Playwright APIRequestContext |
| DB client | psycopg2-binary >=2.9 |
| Assertions | pytest + assertpy |
| Fake data | Faker |
| Reporting | pytest-html + Allure |
| Parallel | pytest-xdist |
| Retry | pytest-rerunfailures |
| Config | python-dotenv + Pydantic |
| CI/CD | GitHub Actions |
