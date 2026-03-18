# ABEM Playwright Test Framework

Professional test automation framework for the ABEM (Apartment & Building Expense Management) system using Playwright, pytest, and psycopg2.

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Copy and configure environment
cp .env.example .env
# Edit .env with your actual credentials and URLs

# Run smoke tests
pytest tests/smoke/ -m smoke

# Run API tests
pytest tests/api/ -m api

# Run UI tests
pytest tests/ui/ -m ui

# Run E2E tests
pytest tests/e2e/ -m e2e

# Run all tests in parallel
pytest -n auto

# Run with Allure reporting
pytest --alluredir=allure-results
allure serve allure-results
```

## Directory Structure

- `tests/e2e/` — Full user journey tests (browser + API + DB)
- `tests/api/` — API-layer tests (no browser)
- `tests/ui/` — UI-layer tests (browser required)
- `tests/db/` — Database-layer assertion tests
- `tests/smoke/` — Production smoke suite
- `pages/` — Page Object Models
- `fixtures/` — Shared pytest fixtures
- `utils/` — Utility modules (API client, DB client, data factory)
- `config/` — Configuration loader

## Technology Stack

| Layer | Tool |
|-------|------|
| Test runner | pytest >=8.1 |
| Browser | Playwright (Python) >=1.44 |
| API client | Playwright APIRequestContext |
| DB client | psycopg2-binary >=2.9 |
| Assertions | pytest + assertpy |
| Fake data | Faker |
| Reporting | pytest-html + Allure |
| Parallel | pytest-xdist |
| Retry | pytest-rerunfailures |
| Config | python-dotenv + Pydantic |
| CI/CD | GitHub Actions |
