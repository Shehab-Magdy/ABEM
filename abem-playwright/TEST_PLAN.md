# ABEM — Master Test Plan

**Project:** ABEM — Apartment & Building Expense Management
**Document Type:** Master Test Plan & Implemented Test Cases
**Framework:** pytest · Playwright · Page Object Model
**Language:** Python 3.12
**Reference:** ABEM QA Strategy v2.0 (February 2026)
**Total Implemented Test Cases:** 220+
**Test Layers:** API · Web UI · E2E · Database · Smoke
**Last Updated:** 2026-03-18

---

## Table of Contents

1. [Test Strategy Overview](#1-test-strategy-overview)
2. [Test ID Convention](#2-test-id-convention)
3. [Test Environment](#3-test-environment)
4. [Test Execution](#4-test-execution)
5. [Smoke Tests](#5-smoke-tests)
6. [API Tests — Authentication & Authorization](#6-api-tests--authentication--authorization)
7. [API Tests — Buildings & Apartments](#7-api-tests--buildings--apartments)
8. [API Tests — Expenses](#8-api-tests--expenses)
9. [API Tests — Payments](#9-api-tests--payments)
10. [API Tests — Dashboard](#10-api-tests--dashboard)
11. [API Tests — Notifications](#11-api-tests--notifications)
12. [API Tests — Exports](#12-api-tests--exports)
13. [API Tests — Users & Profile](#13-api-tests--users--profile)
14. [API Tests — Pagination & Filters](#14-api-tests--pagination--filters)
15. [API Tests — Security](#15-api-tests--security)
16. [Web UI Tests — Authentication](#16-web-ui-tests--authentication)
17. [Web UI Tests — Buildings](#17-web-ui-tests--buildings)
18. [Web UI Tests — Expenses](#18-web-ui-tests--expenses)
19. [Web UI Tests — Payments](#19-web-ui-tests--payments)
20. [Web UI Tests — Dashboard](#20-web-ui-tests--dashboard)
21. [Web UI Tests — Notifications](#21-web-ui-tests--notifications)
22. [Web UI Tests — Profile](#22-web-ui-tests--profile)
23. [Web UI Tests — Exports](#23-web-ui-tests--exports)
24. [Web UI Tests — Performance](#24-web-ui-tests--performance)
25. [Web UI Tests — Accessibility](#25-web-ui-tests--accessibility)
26. [E2E Tests — User Journeys](#26-e2e-tests--user-journeys)
27. [Database Tests](#27-database-tests)
28. [Coverage Traceability Matrix](#28-coverage-traceability-matrix)

---

## 1. Test Strategy Overview

Quality is built into every sprint. Tests are written alongside features, not after. The framework follows three core principles from the ABEM QA Strategy v2:

- **Shift Left:** Tests are specified before implementation starts — acceptance criteria drive test cases.
- **Risk-Based:** Financial calculations, RBAC, and tenant data isolation are highest priority. A bug in the payment split engine or a RBAC bypass affects real money across all tenants.
- **Full-Stack:** Every feature is verified independently at API, Web UI, and Database layers. A bug cannot hide in one layer while passing another.

### Test Layer Strategy

| Layer | Tool | What It Validates | Trigger |
|-------|------|-------------------|---------|
| API | pytest + Playwright APIRequestContext | Business logic, auth, RBAC, data integrity, security | Every commit |
| Web UI | Playwright + POM pattern | User flows, rendering, form validation, accessibility | Every commit |
| E2E | Playwright (API + UI combined) | Full user journeys across multiple modules | Every PR |
| Database | pytest + psycopg2 | Schema integrity, data consistency, constraint enforcement | Every commit |
| Smoke | pytest (API + UI) | Quick production health checks post-deployment | Post-deploy |
| Performance | Playwright timing APIs | Page load times, response time thresholds | Every commit |

---

## 2. Test ID Convention

Every test case follows a consistent ID format used in pytest markers, reports, and this document:

| Format | Example | Meaning |
|--------|---------|---------|
| `TC-API-AUTH-{###}` | TC-API-AUTH-001 | API layer, Authentication module, case #1 |
| `TC-API-BLD-{###}` | TC-API-BLD-001 | API layer, Buildings module, case #1 |
| `TC-API-EXP-{###}` | TC-API-EXP-001 | API layer, Expenses module, case #1 |
| `TC-API-PAY-{###}` | TC-API-PAY-001 | API layer, Payments module, case #1 |
| `TC-API-SEC-{###}` | TC-API-SEC-001 | API layer, Security module, case #1 |
| `TC-UI-AUTH-{###}` | TC-UI-AUTH-001 | Web UI layer, Authentication module, case #1 |
| `TC-UI-BLD-{###}` | TC-UI-BLD-001 | Web UI layer, Buildings module, case #1 |
| `TC-E2E-{###}` | TC-E2E-001 | End-to-end journey, case #1 |
| `TC-DB-{###}` | TC-DB-001 | Database layer, case #1 |
| `TC-SMOKE-{###}` | TC-SMOKE-001 | Production smoke, case #1 |

---

## 3. Test Environment

### Configuration

| Parameter | Value |
|-----------|-------|
| Browser | Chromium (headless) |
| Viewport | 1280 × 720 |
| Locale | en-US |
| Timezone | Africa/Cairo |
| Default Timeout | 30,000 ms |
| Navigation Timeout | 60,000 ms |
| Expect Timeout | 10,000 ms |
| Frontend URL | `http://localhost:5173` |
| Backend API URL | `http://localhost:8000` |
| Database | PostgreSQL on `localhost:5432`, database `abem` |

### Test Users

| Role | Email | Purpose |
|------|-------|---------|
| Admin | `admin@abem.test` | Primary admin for all admin operations |
| Owner | `owner@abem.test` | Primary owner for read-only and RBAC tests |
| Admin2 | `admin2@abem.test` | Second admin for multi-tenant isolation tests |

### Test Data Strategy

- **Factory fixtures:** `create_building`, `create_expense`, `create_payment`, `create_user` return callables for flexible test data creation with auto-cleanup on teardown.
- **Seeded fixtures:** `seeded_building`, `seeded_expense`, `seeded_payment` pre-create complete data graphs.
- **Data builders:** `data_factory.py` generates random but valid payloads using `uuid4` prefixes.
- **Decimal precision:** All monetary values use `Decimal` type — never floats.

---

## 4. Test Execution

```bash
# Run all tests
pytest

# Run by marker
pytest -m smoke              # Quick health-check suite (15 tests)
pytest -m api                # API-layer tests (100+ tests)
pytest -m ui                 # UI-layer tests (30+ tests)
pytest -m e2e                # End-to-end journeys (7 tests)
pytest -m db                 # Database tests (15+ tests)
pytest -m security           # Security tests (30+ tests)
pytest -m performance        # Performance tests (4 tests)
pytest -m accessibility      # Accessibility tests (4 tests)

# Run by feature
pytest -m auth               # Authentication tests
pytest -m buildings          # Building management tests
pytest -m expenses           # Expense management tests
pytest -m payments           # Payment management tests
pytest -m notifications      # Notification system tests
pytest -m exports            # Data export tests

# Run by path
pytest tests/smoke/
pytest tests/api/auth/
pytest tests/ui/buildings/
pytest tests/e2e/
pytest tests/db/
```

---

## 5. Smoke Tests

**File:** `tests/smoke/test_production_smoke.py`
**Class:** `TestProductionSmoke`
**Markers:** `@pytest.mark.smoke`
**Purpose:** Quick post-deployment health checks — all critical paths verified in under 3 minutes.

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-SMOKE-001 | Login API works | Verify the login endpoint returns a successful response with valid admin credentials | P0 | 1. POST `/api/v1/auth/login/` with valid admin email and password | HTTP 200 returned |
| TC-SMOKE-002 | List buildings | Verify the buildings list endpoint is accessible to authenticated admin | P0 | 1. Authenticate as admin; 2. GET `/api/v1/buildings/` | HTTP 200 returned |
| TC-SMOKE-003 | List apartments | Verify the apartments list endpoint is accessible | P0 | 1. Authenticate as admin; 2. GET `/api/v1/apartments/` | HTTP 200 returned |
| TC-SMOKE-004 | List expenses | Verify the expenses list endpoint is accessible | P0 | 1. Authenticate as admin; 2. GET `/api/v1/expenses/` | HTTP 200 returned |
| TC-SMOKE-005 | List payments | Verify the payments list endpoint is accessible | P0 | 1. Authenticate as admin; 2. GET `/api/v1/payments/` | HTTP 200 returned |
| TC-SMOKE-006 | List notifications | Verify the notifications list endpoint is accessible | P1 | 1. Authenticate as admin; 2. GET `/api/v1/notifications/` | HTTP 200 returned |
| TC-SMOKE-007 | List categories | Verify the expense categories endpoint is accessible | P1 | 1. Authenticate as admin; 2. GET `/api/v1/expenses/categories/` | HTTP 200 returned |
| TC-SMOKE-008 | List audit logs | Verify the audit log endpoint is accessible to admin | P1 | 1. Authenticate as admin; 2. GET `/api/v1/audit/` | HTTP 200 returned |
| TC-SMOKE-009 | Admin dashboard | Verify the admin dashboard endpoint returns data | P0 | 1. Authenticate as admin; 2. GET `/api/v1/dashboard/admin/` | HTTP 200 returned |
| TC-SMOKE-010 | Owner dashboard | Verify the owner dashboard endpoint returns data | P0 | 1. Authenticate as owner; 2. GET `/api/v1/dashboard/owner/` | HTTP 200 returned |
| TC-SMOKE-011 | Profile endpoint | Verify the user profile endpoint is accessible | P1 | 1. Authenticate as admin; 2. GET `/api/v1/auth/profile/` | HTTP 200 returned |
| TC-SMOKE-012 | Export CSV | Verify the payment export endpoint returns data | P1 | 1. Authenticate as admin; 2. GET `/api/v1/exports/payments/` | HTTP 200 returned |
| TC-SMOKE-013 | Owner cannot access admin endpoints | Verify RBAC enforcement — owner blocked from admin-only endpoints | P0 | 1. Authenticate as owner; 2. GET `/api/v1/users/` | HTTP 403 returned |
| TC-SMOKE-014 | UI login page loads | Verify the login page renders correctly in the browser | P0 | 1. Navigate to `/login`; 2. Check for Sign in button | Sign in button is visible on the page |
| TC-SMOKE-015 | UI dashboard loads after login | Verify authenticated dashboard page loads successfully | P0 | 1. Login as admin via stored browser state; 2. Navigate to `/dashboard` | Dashboard page loads without errors |

---

## 6. API Tests — Authentication & Authorization

### 6.1 Login

**File:** `tests/api/auth/test_login.py`
**Class:** `TestLogin`
**Markers:** `@pytest.mark.api`, `@pytest.mark.auth`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-AUTH-001 | Valid admin login | Verify admin can login with valid credentials and receives all required tokens | P0 | 1. POST `/api/v1/auth/login/` with valid admin email and password | HTTP 200; response body contains `access`, `refresh`, and `user` fields |
| TC-API-AUTH-002 | JWT contains correct claims | Verify the access token JWT contains the required claims for authorization | P0 | 1. Login as admin; 2. Decode the access token (unverified) | JWT payload contains `user_id`, `role`, and `exp` claims |
| TC-API-AUTH-003 | Admin role in JWT | Verify the admin user receives a JWT with the admin role claim | P0 | 1. Login as admin; 2. Decode access token; 3. Read role claim | `role` claim equals `"admin"` |
| TC-API-AUTH-004 | Owner role in JWT | Verify the owner user receives a JWT with the owner role claim | P0 | 1. Login as owner; 2. Decode access token; 3. Read role claim | `role` claim equals `"owner"` |
| TC-API-AUTH-005 | Wrong password rejected | Verify login fails with incorrect password | P0 | 1. POST `/api/v1/auth/login/` with valid email but wrong password | HTTP 401 returned |
| TC-API-AUTH-006 | Nonexistent email rejected | Verify login fails with an email that doesn't exist in the system | P0 | 1. POST `/api/v1/auth/login/` with a non-registered email | HTTP 401 returned |
| TC-API-AUTH-007 | Empty email rejected | Verify login fails when email field is empty | P1 | 1. POST `/api/v1/auth/login/` with empty email string | HTTP 400 or 401 returned |
| TC-API-AUTH-008 | Empty password rejected | Verify login fails when password field is empty | P1 | 1. POST `/api/v1/auth/login/` with empty password string | HTTP 400 or 401 returned |
| TC-API-AUTH-009 | Missing email field rejected | Verify login fails when email field is omitted from request body | P1 | 1. POST `/api/v1/auth/login/` with body containing only password | HTTP 400 returned |
| TC-API-AUTH-010 | Missing password field rejected | Verify login fails when password field is omitted from request body | P1 | 1. POST `/api/v1/auth/login/` with body containing only email | HTTP 400 returned |
| TC-API-AUTH-011 | Error does not reveal email existence | Verify the error message for wrong password is identical to the error for nonexistent email (anti-enumeration) | P0 | 1. POST login with wrong password → capture error; 2. POST login with nonexistent email → capture error; 3. Compare error messages | Both requests return HTTP 401 with identical error messages |

### 6.2 Logout

**File:** `tests/api/auth/test_logout.py`
**Class:** `TestLogout`
**Markers:** `@pytest.mark.api`, `@pytest.mark.auth`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-AUTH-012 | Valid logout | Verify logout succeeds with a valid refresh token | P0 | 1. Login as admin; 2. POST `/api/v1/auth/logout/` with refresh token | HTTP 200, 204, or 205 returned |
| TC-API-AUTH-013 | Logout blacklists refresh token | Verify that a refresh token cannot be reused after logout | P0 | 1. Login; 2. Logout; 3. POST `/api/v1/auth/token/refresh/` with the same refresh token | HTTP 401 returned on refresh attempt |
| TC-API-AUTH-014 | Logout without refresh token | Verify logout fails when no refresh token is provided | P1 | 1. POST `/api/v1/auth/logout/` with empty body | HTTP 400 or 401 returned |
| TC-API-AUTH-015 | Logout with invalid refresh token | Verify logout fails when an invalid/malformed refresh token is sent | P1 | 1. POST `/api/v1/auth/logout/` with an invalid token string | HTTP 400 or 401 returned |

### 6.3 Token Refresh

**File:** `tests/api/auth/test_token_refresh.py`
**Class:** `TestTokenRefresh`
**Markers:** `@pytest.mark.api`, `@pytest.mark.auth`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-AUTH-016 | Valid token refresh | Verify a valid refresh token generates a new access token | P0 | 1. Login; 2. POST `/api/v1/auth/token/refresh/` with valid refresh token | HTTP 200; response contains new `access` token |
| TC-API-AUTH-017 | Invalid refresh token rejected | Verify refresh fails with an invalid token | P0 | 1. POST `/api/v1/auth/token/refresh/` with invalid token | HTTP 401 returned |
| TC-API-AUTH-018 | Refresh token rotation | Verify the old refresh token is blacklisted after a successful refresh (rotation) | P0 | 1. Login; 2. Refresh token; 3. Try to refresh again with the original refresh token | HTTP 401 on second refresh attempt |
| TC-API-AUTH-019 | Refreshed token has valid claims | Verify the new access token from a refresh contains the correct claims | P1 | 1. Login; 2. Refresh; 3. Decode new access token | New token contains `role`, `user_id`, and `exp` claims |

### 6.4 Account Lockout

**File:** `tests/api/auth/test_account_lockout.py`
**Class:** `TestAccountLockout`
**Markers:** `@pytest.mark.api`, `@pytest.mark.auth`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-AUTH-020 | Four failed attempts — still unlocked | Verify that 4 failed login attempts do not lock the account | P0 | 1. Create temp user; 2. Attempt login with wrong password 4 times; 3. Login with correct password | HTTP 200 on correct login after 4 failures |
| TC-API-AUTH-021 | Fifth failed attempt triggers lockout | Verify that the 5th consecutive failed login locks the account | P0 | 1. Create temp user; 2. Attempt login with wrong password 5 times | HTTP 423 or 429 returned on the 5th attempt |
| TC-API-AUTH-022 | Correct password after lockout still rejected | Verify that a locked account rejects even correct credentials | P0 | 1. Lock account (5 failed attempts); 2. Try login with correct password | HTTP 423 or 429 returned |
| TC-API-AUTH-023 | Admin can reactivate locked account | Verify that an admin can reactivate a locked user account | P0 | 1. Lock user account; 2. Admin activates user via API; 3. User logs in | Login succeeds with HTTP 200 after admin activation |

---

## 7. API Tests — Buildings & Apartments

### 7.1 Building CRUD

**File:** `tests/api/buildings/test_building_crud.py`
**Class:** `TestBuildingCRUD`
**Markers:** `@pytest.mark.api`, `@pytest.mark.buildings`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-BLD-001 | Create building with required fields | Verify admin can create a building with mandatory fields | P0 | 1. POST `/api/v1/buildings/` with name, address, city, country, num_floors, num_apartments | HTTP 201; response contains `id` and `name` |
| TC-API-BLD-002 | Create building with all fields | Verify admin can create a building with all optional fields included | P1 | 1. POST `/api/v1/buildings/` with all required and optional fields | HTTP 201 returned |
| TC-API-BLD-003 | List buildings | Verify the buildings list endpoint returns paginated results | P0 | 1. GET `/api/v1/buildings/` | HTTP 200; response has `count` and `results` keys |
| TC-API-BLD-004 | Get building by ID | Verify a single building can be retrieved by its ID | P0 | 1. Create building; 2. GET `/api/v1/buildings/{id}/` | HTTP 200 returned with building data |
| TC-API-BLD-005 | Update building | Verify admin can update a building's name via PATCH | P1 | 1. Create building; 2. PATCH `/api/v1/buildings/{id}/` with new name | HTTP 200; `name` field reflects updated value |
| TC-API-BLD-006 | Delete building (soft delete) | Verify admin can soft-delete a building and it returns 404 on subsequent GET | P0 | 1. Create building; 2. DELETE `/api/v1/buildings/{id}/`; 3. GET the same building | DELETE returns 200/204; subsequent GET returns 404 |
| TC-API-BLD-007 | Create building missing name | Verify validation rejects a building creation without a name | P1 | 1. POST `/api/v1/buildings/` without the `name` field | HTTP 400 returned |
| TC-API-BLD-008 | Create building missing address | Verify validation rejects a building creation without an address | P1 | 1. POST `/api/v1/buildings/` without the `address` field | HTTP 400 returned |
| TC-API-BLD-009 | Create building with zero floors | Verify validation rejects `num_floors=0` | P2 | 1. POST `/api/v1/buildings/` with `num_floors=0` | HTTP 400 returned |
| TC-API-BLD-010 | Get nonexistent building | Verify 404 is returned for a nonexistent building ID | P2 | 1. GET `/api/v1/buildings/{random-uuid}/` | HTTP 404 returned |
| TC-API-BLD-011 | Owner cannot create building | Verify RBAC — owner role is forbidden from creating buildings | P0 | 1. Authenticate as owner; 2. POST `/api/v1/buildings/` | HTTP 403 returned |
| TC-API-BLD-012 | Unauthenticated create rejected | Verify unauthenticated requests are rejected | P0 | 1. POST `/api/v1/buildings/` without auth header | HTTP 401 returned |
| TC-API-BLD-013 | Owner cannot delete building | Verify RBAC — owner role is forbidden from deleting buildings | P0 | 1. Authenticate as owner; 2. DELETE `/api/v1/buildings/{id}/` | HTTP 403 returned |

### 7.2 Building Isolation

**File:** `tests/api/buildings/test_building_isolation.py`
**Class:** `TestBuildingIsolation`
**Markers:** `@pytest.mark.api`, `@pytest.mark.buildings`, `@pytest.mark.tenant_isolation`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-BLD-014 | Admin cannot read other admin's buildings | Verify multi-tenant isolation — Admin B cannot access Admin A's building | P0 | 1. Admin A creates building; 2. Admin B attempts GET on that building | HTTP 403 or 404 returned |
| TC-API-BLD-015 | Admin cannot create expense in other admin's building | Verify cross-tenant expense creation is blocked | P0 | 1. Admin A creates building; 2. Admin B POST expense to that building | HTTP 400 or 403 returned (201 indicates isolation gap) |
| TC-API-BLD-016 | Building creates 15 default categories | Verify that creating a building auto-seeds 15 default expense categories | P1 | 1. Create building; 2. GET categories for that building | 15 categories returned |
| TC-API-BLD-017 | Building auto-creates apartments | Verify that `num_apartments` and `num_stores` auto-create the correct number of units | P1 | 1. Create building with num_apartments=2, num_stores=1; 2. GET apartments for that building | At least 3 apartments/stores returned |

### 7.3 Apartment CRUD

**File:** `tests/api/apartments/test_apartment_crud.py`
**Class:** `TestApartmentCRUD`
**Markers:** `@pytest.mark.api`, `@pytest.mark.apartments`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-APT-001 | Create apartment | Verify admin can create an apartment within a building | P0 | 1. Create building; 2. POST `/api/v1/apartments/` with building_id and unit_number | HTTP 201 returned |
| TC-API-APT-002 | List apartments by building | Verify apartments can be listed filtered by building | P0 | 1. Create building with auto-apartments; 2. GET `/api/v1/apartments/?building_id={id}` | HTTP 200; at least 2 results |
| TC-API-APT-003 | Get apartment by ID | Verify a single apartment can be retrieved | P1 | 1. GET `/api/v1/apartments/{id}/` | HTTP 200 returned |
| TC-API-APT-004 | Update apartment | Verify admin can update an apartment via PATCH | P1 | 1. PATCH `/api/v1/apartments/{id}/` with updated fields | HTTP 200 returned |
| TC-API-APT-005 | Delete apartment | Verify admin can delete an apartment | P1 | 1. DELETE `/api/v1/apartments/{id}/` | HTTP 200 or 204 returned |
| TC-API-APT-006 | Create without building_id rejected | Verify validation requires building_id | P2 | 1. POST `/api/v1/apartments/` without building_id | HTTP 400 returned |
| TC-API-APT-007 | Create without unit_number rejected | Verify validation requires unit_number | P2 | 1. POST `/api/v1/apartments/` without unit_number | HTTP 400 returned |
| TC-API-APT-008 | Duplicate unit_number rejected | Verify uniqueness constraint on unit_number within a building | P1 | 1. Create apartment; 2. Create another with the same unit_number in the same building | HTTP 400 or 409 returned |
| TC-API-APT-009 | Owner cannot create apartment | Verify RBAC — owner cannot create apartments | P0 | 1. POST apartment as owner | HTTP 403 returned |
| TC-API-APT-010 | Get nonexistent apartment | Verify 404 for nonexistent apartment | P2 | 1. GET `/api/v1/apartments/{random-uuid}/` | HTTP 404 returned |

### 7.4 Apartment Type Split

**File:** `tests/api/apartments/test_apartment_type_split.py`
**Class:** `TestApartmentTypeSplit`
**Markers:** `@pytest.mark.api`, `@pytest.mark.apartments`, `@pytest.mark.expenses`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-APT-011 | Filter apartments by type — apartment | Verify filtering returns only apartment-type units | P1 | 1. GET apartments with `unit_type=apartment` filter | HTTP 200; all results have `unit_type == "apartment"` |
| TC-API-APT-012 | Filter apartments by type — store | Verify filtering returns only store-type units | P1 | 1. GET apartments with `unit_type=store` filter | HTTP 200; all results have `unit_type == "store"` |
| TC-API-APT-013 | Apartments-only split excludes stores | Verify `equal_apartments` split type does not assign shares to stores | P0 | 1. Create building with 2 apartments and 1 store; 2. POST expense with `split_type=equal_apartments` | Shares are only assigned to apartments; stores have no shares |
| TC-API-APT-014 | Stores-only split excludes apartments | Verify `equal_stores` split type does not assign shares to apartments | P0 | 1. Create building with 2 apartments and 1 store; 2. POST expense with `split_type=equal_stores` | Shares are only assigned to stores; apartments have no shares |

---

## 8. API Tests — Expenses

### 8.1 Expense CRUD

**File:** `tests/api/expenses/test_expense_crud.py`
**Class:** `TestExpenseCRUD`
**Markers:** `@pytest.mark.api`, `@pytest.mark.expenses`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-EXP-001 | Create expense with required fields | Verify admin can create an expense with mandatory fields and shares are generated | P0 | 1. POST `/api/v1/expenses/` with building_id, category_id, amount, title, split_type | HTTP 201; response contains `apartment_shares` |
| TC-API-EXP-002 | Create expense with all fields | Verify expense creation with all optional fields (description, due_date, recurring, frequency) | P1 | 1. POST expense with all fields populated | HTTP 201 returned |
| TC-API-EXP-003 | List expenses | Verify expenses list endpoint returns results | P0 | 1. GET `/api/v1/expenses/` | HTTP 200; response contains `results` key |
| TC-API-EXP-004 | Get expense by ID | Verify single expense retrieval | P1 | 1. GET `/api/v1/expenses/{id}/` | HTTP 200 returned |
| TC-API-EXP-005 | Update expense | Verify admin can update an expense title | P1 | 1. PATCH `/api/v1/expenses/{id}/` with new title | HTTP 200; title updated in response |
| TC-API-EXP-006 | Soft-delete expense | Verify expense is soft-deleted and returns 404 on subsequent GET | P0 | 1. DELETE `/api/v1/expenses/{id}/`; 2. GET the same expense | DELETE returns 200/204; GET returns 404 |
| TC-API-EXP-007 | Missing building_id rejected | Verify validation requires building_id | P1 | 1. POST expense without building_id | HTTP 400 returned |
| TC-API-EXP-008 | Missing amount rejected | Verify validation requires amount | P1 | 1. POST expense without amount | HTTP 400 returned |
| TC-API-EXP-009 | Negative amount rejected | Verify validation rejects negative amounts | P0 | 1. POST expense with `amount=-100` | HTTP 400 returned |
| TC-API-EXP-010 | Zero amount rejected | Verify validation rejects zero amount | P0 | 1. POST expense with `amount=0` | HTTP 400 returned |
| TC-API-EXP-011 | String amount rejected | Verify validation rejects non-numeric amount values | P2 | 1. POST expense with `amount="abc"` | HTTP 400 returned |
| TC-API-EXP-012 | Owner cannot create expense | Verify RBAC — owner is forbidden from creating expenses | P0 | 1. POST expense as owner | HTTP 403 returned |
| TC-API-EXP-013 | Unauthenticated create rejected | Verify unauthenticated expense creation is blocked | P0 | 1. POST expense without auth header | HTTP 401 returned |
| TC-API-EXP-014 | Get nonexistent expense | Verify 404 for nonexistent expense | P2 | 1. GET `/api/v1/expenses/{random-uuid}/` | HTTP 404 returned |

### 8.2 Equal Split Engine

**File:** `tests/api/expenses/test_expense_split_equal.py`
**Class:** `TestExpenseSplitEqual`
**Markers:** `@pytest.mark.api`, `@pytest.mark.expenses`, `@pytest.mark.boundary`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-EXP-015 | Amount exactly divisible | Verify equal split with no remainder distributes evenly | P0 | 1. Create expense with amount=100 split across 2 units | Each unit receives share of 50 |
| TC-API-EXP-016 | Amount produces remainder — round up to 5 | Verify the round-up-to-5 logic when amount is not exactly divisible | P0 | 1. Create expense with amount=101 split across 2 units | Each share rounds up to 55 (ceil(50.5/5)*5) |
| TC-API-EXP-017 | Amount 99 split by 2 | Verify boundary rounding for amount=99 across 2 units | P1 | 1. Create expense with amount=99, 2 units | Each share = 50 (ceil(49.5/5)*5) |
| TC-API-EXP-018 | Single unit gets full amount | Verify a single-unit building assigns the full (rounded) amount to that unit | P0 | 1. Create building with 1 apartment; 2. Create expense with amount=101 | Share = 105 (ceil(101/5)*5) |
| TC-API-EXP-019 | Shares sum always >= amount | Verify the total of all shares is always greater than or equal to the expense amount (parametrized: 101, 203, 999, 1) | P0 | 1. Create expense with each amount; 2. Sum all apartment shares | Sum of shares >= expense amount for every case |
| TC-API-EXP-020 | Minimum amount 0.01 accepted | Verify the minimum valid expense amount is accepted | P2 | 1. POST expense with `amount=0.01` | HTTP 201 returned |
| TC-API-EXP-021 | Negative amount rejected (boundary) | Verify negative amount is rejected at the split level | P0 | 1. POST expense with `amount=-1` | HTTP 400 returned |
| TC-API-EXP-022 | Zero amount rejected (boundary) | Verify zero amount is rejected at the split level | P0 | 1. POST expense with `amount=0` | HTTP 400 returned |
| TC-API-EXP-023 | Null amount rejected | Verify null amount is rejected | P1 | 1. POST expense with `amount=null` | HTTP 400 returned |
| TC-API-EXP-024 | String amount rejected (boundary) | Verify string amount is rejected at the split level | P2 | 1. POST expense with `amount="abc"` | HTTP 400 returned |

### 8.3 Split by Type

**File:** `tests/api/expenses/test_expense_split_by_type.py`
**Class:** `TestExpenseSplitByType`
**Markers:** `@pytest.mark.api`, `@pytest.mark.expenses`, `@pytest.mark.boundary`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-EXP-025 | Apartments-only split excludes stores | Verify `equal_apartments` split assigns shares only to apartments | P0 | 1. Create building with apartments and stores; 2. POST expense with `split_type=equal_apartments` | Share IDs and store IDs have no overlap |
| TC-API-EXP-026 | Stores-only split excludes apartments | Verify `equal_stores` split assigns shares only to stores | P0 | 1. Create building with apartments and stores; 2. POST expense with `split_type=equal_stores` | Share IDs and apartment IDs have no overlap |
| TC-API-EXP-027 | Apartment shares sum >= amount | Verify apartments-only split totals meet or exceed expense amount | P0 | 1. Create expense amount=201 with `split_type=equal_apartments` | Sum of apartment shares >= 201 |
| TC-API-EXP-028 | Store balance unchanged after apartments-only expense | Verify stores are not affected by an apartments-only expense | P0 | 1. Get store balance before; 2. Create apartments-only expense; 3. Get store balance after | Store balance before == store balance after |

### 8.4 Expense Participation (Custom Split)

**File:** `tests/api/expenses/test_expense_participation.py`
**Class:** `TestExpenseParticipation`
**Markers:** `@pytest.mark.api`, `@pytest.mark.expenses`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-EXP-029 | Custom split — specific apartments | Verify custom split only assigns shares to selected apartments | P0 | 1. Create building with 3 apartments; 2. POST expense with `split_type=custom` selecting 2 apartments | Only 2 shares created; third apartment excluded |
| TC-API-EXP-030 | Custom split — weighted allocation | Verify custom split with weighted allocation distributes correctly | P1 | 1. Create expense with custom weights (2.0:1.0) | Sum of all shares >= expense amount |

### 8.5 Recurring Expenses

**File:** `tests/api/expenses/test_expense_recurring.py`
**Class:** `TestExpenseRecurring`
**Markers:** `@pytest.mark.api`, `@pytest.mark.expenses`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-EXP-031 | Create recurring expense | Verify creating an expense with `is_recurring=true` | P1 | 1. POST expense with `is_recurring=true`, `frequency=monthly` | HTTP 201; `is_recurring == true` in response |
| TC-API-EXP-032 | Recurring expense has config | Verify recurring expense stores frequency configuration | P1 | 1. POST expense with `is_recurring=true`, `frequency=quarterly` | Response has `recurring_config` with `frequency=quarterly` |
| TC-API-EXP-033 | Recurring without frequency rejected | Verify validation requires frequency when recurring is enabled | P1 | 1. POST expense with `is_recurring=true` but no frequency | HTTP 400 returned |
| TC-API-EXP-034 | Non-recurring ignores frequency | Verify non-recurring expense ignores the frequency field | P2 | 1. POST expense with `is_recurring=false` and `frequency=annual` | HTTP 201; `is_recurring == false` |

### 8.6 Expense File Upload

**File:** `tests/api/expenses/test_expense_file_upload.py`
**Class:** `TestExpenseFileUpload`
**Markers:** `@pytest.mark.api`, `@pytest.mark.file_upload`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-EXP-035 | Upload JPEG bill | Verify JPEG file upload succeeds for an expense | P0 | 1. Create expense; 2. POST multipart JPEG to `/api/v1/expenses/{id}/upload/` | HTTP 200 or 201 |
| TC-API-EXP-036 | Upload PDF bill | Verify PDF file upload succeeds for an expense | P1 | 1. Create expense; 2. POST multipart PDF to upload endpoint | HTTP 200 or 201 |
| TC-API-EXP-037 | EXE file rejected | Verify executable files are blocked by magic-bytes validation | P0 | 1. Create expense; 2. POST multipart EXE file | HTTP 400 returned |
| TC-API-EXP-038 | Oversized file rejected | Verify files exceeding 10 MB are rejected | P0 | 1. Create expense; 2. POST multipart file > 10 MB | HTTP 413 returned |
| TC-API-EXP-039 | Empty upload body rejected | Verify empty upload request is rejected | P2 | 1. POST empty data to upload endpoint | HTTP 400 or 415 returned |
| TC-API-EXP-040 | Unauthenticated upload rejected | Verify unauthenticated file upload is blocked | P0 | 1. POST file without Authorization header | HTTP 401 returned |
| TC-API-EXP-041 | Owner cannot upload | Verify RBAC — owner is forbidden from uploading bill files | P0 | 1. POST file as owner | HTTP 403 returned |

### 8.7 Expense Categories

**File:** `tests/api/expenses/test_expense_categories.py`
**Class:** `TestExpenseCategories`
**Markers:** `@pytest.mark.api`, `@pytest.mark.categories`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-CAT-001 | List building categories | Verify listing categories for a building returns default seeded categories | P0 | 1. GET `/api/v1/expenses/categories/` with building_id | HTTP 200; 15 default categories returned |
| TC-API-CAT-002 | Category has required fields | Verify each category has `id`, `name`, `icon`, and `color` | P1 | 1. GET categories; 2. Check fields on each category | All categories contain required fields |
| TC-API-CAT-003 | Create expense with valid category | Verify an expense can be created using an existing category | P0 | 1. Get categories; 2. POST expense with first category's ID | HTTP 201 returned |
| TC-API-CAT-004 | Invalid category ID rejected | Verify creating an expense with a nonexistent category fails | P1 | 1. POST expense with a random UUID as category_id | HTTP 400 returned |
| TC-API-CAT-005 | Admin creates custom category | Verify admin can create a new custom expense category | P1 | 1. POST custom category with name and building_id | HTTP 201; response name matches payload |
| TC-API-CAT-006 | Custom category appears in list | Verify a newly created category appears in the category list | P1 | 1. Create custom category; 2. GET categories list | Created category name found in list |
| TC-API-CAT-007 | Duplicate category name rejected | Verify duplicate category names within a building are rejected | P1 | 1. Create category "X"; 2. Create another "X" in same building | HTTP 400 or 409 returned |
| TC-API-CAT-008 | Owner cannot create category | Verify RBAC — owner cannot create categories | P0 | 1. POST category as owner | HTTP 403 returned |
| TC-API-CAT-009 | Owner cannot delete category | Verify RBAC — owner cannot delete categories | P0 | 1. Admin creates category; 2. Owner tries DELETE | HTTP 403 returned |

---

## 9. API Tests — Payments

### 9.1 Payment Recording

**File:** `tests/api/payments/test_payment_recording.py`
**Class:** `TestPaymentRecording`
**Markers:** `@pytest.mark.api`, `@pytest.mark.payments`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-PAY-001 | Record payment success | Verify admin can record a payment with valid data | P0 | 1. POST `/api/v1/payments/` with apartment_id, amount_paid=50, payment_method=cash | HTTP 201; response has `id`, `balance_before`, `balance_after` |
| TC-API-PAY-002 | Payment updates balance | Verify balance is reduced by the payment amount | P0 | 1. POST payment with amount_paid=30 | `balance_after == balance_before - 30` |
| TC-API-PAY-003 | Payment with all methods | Verify each payment method (cash, bank_transfer, cheque) is accepted (parametrized) | P1 | 1. POST payment with each method | HTTP 201; `payment_method` matches for each |
| TC-API-PAY-004 | Zero amount rejected | Verify validation rejects zero payment amount | P0 | 1. POST payment with `amount_paid=0` | HTTP 400 returned |
| TC-API-PAY-005 | Negative amount rejected | Verify validation rejects negative payment amount | P0 | 1. POST payment with `amount_paid=-50` | HTTP 400 returned |
| TC-API-PAY-006 | Missing apartment_id rejected | Verify validation requires apartment_id | P1 | 1. POST payment without apartment_id | HTTP 400 returned |
| TC-API-PAY-007 | Nonexistent apartment rejected | Verify payment fails for a nonexistent apartment | P1 | 1. POST payment with random UUID as apartment_id | HTTP 400 or 404 returned |
| TC-API-PAY-008 | Invalid payment method rejected | Verify validation rejects unknown payment methods | P1 | 1. POST payment with `payment_method="bitcoin"` | HTTP 400 returned |
| TC-API-PAY-009 | Owner cannot record payment | Verify RBAC — owner is forbidden from recording payments | P0 | 1. POST payment as owner | HTTP 403 returned |
| TC-API-PAY-010 | Unauthenticated payment rejected | Verify unauthenticated payment recording is blocked | P0 | 1. POST payment without auth header | HTTP 401 returned |

### 9.2 Balance Calculation

**File:** `tests/api/payments/test_balance_calculation.py`
**Class:** `TestBalanceCalculation`
**Markers:** `@pytest.mark.api`, `@pytest.mark.payments`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-PAY-011 | Balance after single payment | Verify balance is correctly reduced after a single payment | P0 | 1. POST payment with amount_paid=25 | `balance_after == balance_before - Decimal("25")` |
| TC-API-PAY-012 | Balance after multiple payments | Verify sequential payments accumulate correctly | P0 | 1. POST first payment (10); 2. POST second payment (15) | `p2.balance_before == p1.balance_after`; `p2.balance_after == p1.balance_after - 15` |
| TC-API-PAY-013 | Payment immutable — no PATCH | Verify payments cannot be modified after recording | P0 | 1. PATCH existing payment with new amount | HTTP 405, 403, or 404 returned |
| TC-API-PAY-014 | Payment immutable — no DELETE | Verify payments cannot be deleted | P0 | 1. DELETE existing payment | HTTP 405, 403, or 404 returned |
| TC-API-PAY-015 | Balance before snapshot correct | Verify the balance_before snapshot matches the apartment's actual balance at payment time | P0 | 1. Get apartment balance; 2. Record payment; 3. Check balance_before in response | `payment.balance_before == apartment balance before payment` |

### 9.3 Overpayment

**File:** `tests/api/payments/test_overpayment.py`
**Class:** `TestOverpayment`
**Markers:** `@pytest.mark.api`, `@pytest.mark.payments`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-PAY-016 | Overpayment creates credit | Verify paying more than owed creates a negative (credit) balance | P0 | 1. Create expense of 100; 2. Pay 150 | `balance_after < 0` |
| TC-API-PAY-017 | Credit carries forward | Verify overpayment credit is automatically applied to the next expense | P0 | 1. Create expense 100; 2. Overpay 150; 3. Create second expense 200; 4. Check balance | Final balance < 200 (credit deducted) |
| TC-API-PAY-018 | Exact payment zeroes balance | Verify paying the exact owed amount results in zero balance | P0 | 1. Create expense; 2. Pay exact balance amount | `balance_after == Decimal("0")` |

### 9.4 Payment Receipt

**File:** `tests/api/payments/test_payment_receipt.py`
**Class:** `TestPaymentReceipt`
**Markers:** `@pytest.mark.api`, `@pytest.mark.payments`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-PAY-019 | Receipt returns PDF | Verify payment receipt endpoint generates a valid PDF | P0 | 1. GET `/api/v1/payments/{id}/receipt/` | HTTP 200; Content-Type contains "pdf"; body is valid PDF |
| TC-API-PAY-020 | Admin can access any receipt | Verify admin can access receipts for any payment | P1 | 1. GET receipt as admin | HTTP 200 returned |
| TC-API-PAY-021 | Nonexistent payment receipt | Verify 404 for a nonexistent payment's receipt | P2 | 1. GET receipt for random UUID | HTTP 404 returned |

---

## 10. API Tests — Dashboard

**File:** `tests/api/dashboard/test_dashboard_aggregations.py`
**Class:** `TestDashboardAggregations`
**Markers:** `@pytest.mark.api`, `@pytest.mark.dashboard`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-DASH-001 | Admin dashboard returns data | Verify admin dashboard endpoint returns aggregated data | P0 | 1. GET `/api/v1/dashboard/admin/` | HTTP 200; response is a dict |
| TC-API-DASH-002 | Admin dashboard with building filter | Verify admin dashboard supports building_id filter | P1 | 1. GET `/api/v1/dashboard/admin/?building_id={id}` | HTTP 200 returned |
| TC-API-DASH-003 | Owner dashboard returns data | Verify owner dashboard endpoint returns owner-specific data | P0 | 1. GET `/api/v1/dashboard/owner/` as owner | HTTP 200 returned |
| TC-API-DASH-004 | Owner cannot access admin dashboard | Verify RBAC — owner is blocked from admin dashboard | P0 | 1. GET `/api/v1/dashboard/admin/` as owner | HTTP 403 returned |
| TC-API-DASH-005 | Dashboard responds within 1s | Verify dashboard API meets performance SLA | P1 | 1. GET dashboard; 2. Measure response time | HTTP 200; response time < 1000 ms |

---

## 11. API Tests — Notifications

### 11.1 Notification Broadcast

**File:** `tests/api/notifications/test_notification_broadcast.py`
**Class:** `TestNotificationBroadcast`
**Markers:** `@pytest.mark.api`, `@pytest.mark.notifications`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-NOTIF-001 | Admin can broadcast | Verify admin can send a broadcast notification to all building owners | P0 | 1. POST `/api/v1/notifications/broadcast/` with building_id, subject, message | HTTP 200 or 201 returned |
| TC-API-NOTIF-002 | Owner cannot broadcast | Verify RBAC — owner is forbidden from broadcasting | P0 | 1. POST broadcast as owner | HTTP 403 returned |

### 11.2 Notification Preferences

**File:** `tests/api/notifications/test_notification_preferences.py`
**Class:** `TestNotificationPreferences`
**Markers:** `@pytest.mark.api`, `@pytest.mark.notifications`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-NOTIF-003 | Get notification preferences | Verify user profile includes notification preferences | P1 | 1. GET `/api/v1/auth/profile/` as owner | HTTP 200; response contains `notification_preferences` or field is optional |
| TC-API-NOTIF-004 | Update notification preferences | Verify user can update their notification preferences | P1 | 1. PATCH profile with `notification_preferences={email_enabled: false}` | HTTP 200 or 204 returned |

### 11.3 Notification Triggers

**File:** `tests/api/notifications/test_notification_triggers.py`
**Class:** `TestNotificationTriggers`
**Markers:** `@pytest.mark.api`, `@pytest.mark.notifications`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-NOTIF-005 | Expense creates notification | Verify creating an expense triggers notifications | P0 | 1. Create seeded expense; 2. GET `/api/v1/notifications/` | HTTP 200 returned |
| TC-API-NOTIF-006 | Payment creates notification | Verify recording a payment triggers notifications | P0 | 1. Create seeded payment; 2. GET `/api/v1/notifications/` | HTTP 200 returned |
| TC-API-NOTIF-007 | Mark notification as read | Verify a notification can be marked as read | P1 | 1. GET unread notifications; 2. POST mark as read; 3. GET notification | is_read == true after marking |

---

## 12. API Tests — Exports

### 12.1 CSV Export

**File:** `tests/api/exports/test_export_csv.py`
**Class:** `TestExportCSV`
**Markers:** `@pytest.mark.api`, `@pytest.mark.exports`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-EXP-CSV-001 | Export payments as CSV | Verify payment data can be exported in CSV format | P0 | 1. GET `/api/v1/exports/payments/` | HTTP 200; Content-Type contains "csv" or "text" |
| TC-API-EXP-CSV-002 | CSV has correct columns | Verify the exported CSV contains expected column headers | P1 | 1. GET payments export; 2. Parse CSV headers | CSV has a header row with column names |
| TC-API-EXP-CSV-003 | CSV data matches API | Verify CSV data rows contain actual payment data | P1 | 1. GET payments export; 2. Parse CSV rows | At least 1 data row present |
| TC-API-EXP-CSV-004 | Empty date range returns header only | Verify export with no matching data returns only headers | P2 | 1. GET export with `date_from=2099-01-01&date_to=2099-12-31` | HTTP 200; CSV has 0 data rows |
| TC-API-EXP-CSV-005 | Owner cannot export | Verify RBAC — owner is forbidden from exporting | P0 | 1. GET export as owner | HTTP 403 returned |

### 12.2 XLSX Export

**File:** `tests/api/exports/test_export_xlsx.py`
**Class:** `TestExportXLSX`
**Markers:** `@pytest.mark.api`, `@pytest.mark.exports`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-EXP-XLSX-001 | Export expenses as XLSX | Verify expense data can be exported in XLSX format | P0 | 1. GET `/api/v1/exports/expenses/?file_format=xlsx&building_id={id}` | HTTP 200; Content-Type contains "spreadsheet", "xlsx", or "octet" |
| TC-API-EXP-XLSX-002 | XLSX has data | Verify the XLSX export contains data rows | P1 | 1. GET XLSX export with seeded data; 2. Parse XLSX | At least 1 row present |
| TC-API-EXP-XLSX-003 | XLSX row count matches API | Verify XLSX row count matches the API expense count | P1 | 1. GET XLSX; 2. GET expenses list; 3. Compare counts | XLSX row count == API expense count |

### 12.3 Export Filters

**File:** `tests/api/exports/test_export_filters.py`
**Class:** `TestExportFilters`
**Markers:** `@pytest.mark.api`, `@pytest.mark.exports`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-EXP-FLT-001 | Export date range filter | Verify export respects date range filtering | P1 | 1. GET export with `date_from=2026-01-01&date_to=2026-12-31` | HTTP 200 returned |
| TC-API-EXP-FLT-002 | Export building scope | Verify export scopes data to a specific building | P1 | 1. GET export with building_id and `file_format=csv` | HTTP 200 returned |
| TC-API-EXP-FLT-003 | Empty date range filter | Verify future date range returns empty export | P2 | 1. GET export with `date_from=2099-01-01&date_to=2099-12-31` | HTTP 200; 0 data rows |

---

## 13. API Tests — Users & Profile

### 13.1 User Management

**File:** `tests/api/users/test_user_management.py`
**Class:** `TestUserManagement`
**Markers:** `@pytest.mark.api`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-USR-001 | Create admin user | Verify admin can create a new user with admin role | P0 | 1. POST `/api/v1/users/` with role=admin | HTTP 201; `role == "admin"` |
| TC-API-USR-002 | Create owner user | Verify admin can create a new user with owner role | P0 | 1. POST `/api/v1/users/` with role=owner | HTTP 201; `role == "owner"` |
| TC-API-USR-003 | List users | Verify users list endpoint returns paginated results | P0 | 1. GET `/api/v1/users/` | HTTP 200; response has `results` key |
| TC-API-USR-004 | Get user by ID | Verify a single user can be retrieved | P1 | 1. GET `/api/v1/users/{id}/` | HTTP 200 returned |
| TC-API-USR-005 | Update user | Verify admin can update a user's first name | P1 | 1. PATCH `/api/v1/users/{id}/` with new first_name | HTTP 200 returned |
| TC-API-USR-006 | Deactivate user | Verify admin can deactivate a user account | P0 | 1. Create user; 2. POST deactivate endpoint | HTTP 200, 204, or 404 returned |
| TC-API-USR-007 | Deactivated user cannot login | Verify a deactivated user is blocked from logging in | P0 | 1. Create user; 2. Deactivate; 3. Attempt login | HTTP 401 on login |
| TC-API-USR-008 | Activate user | Verify admin can reactivate a deactivated user | P0 | 1. Create user; 2. Deactivate; 3. Activate; 4. Login | Login returns HTTP 200 |
| TC-API-USR-009 | Duplicate email rejected | Verify duplicate email registration is rejected | P1 | 1. Create user with email X; 2. Create another with same email | HTTP 400 returned |
| TC-API-USR-010 | Missing email rejected | Verify validation requires email for user creation | P1 | 1. POST user without email field | HTTP 400 returned |
| TC-API-USR-011 | Owner cannot create user | Verify RBAC — owner cannot create users | P0 | 1. POST user as owner | HTTP 403 returned |
| TC-API-USR-012 | Owner cannot list users | Verify RBAC — owner cannot list users | P0 | 1. GET users as owner | HTTP 403 returned |
| TC-API-USR-013 | Password not in response | Verify password is never exposed in API responses | P0 | 1. Create user; 2. GET user by ID | Response does not contain `password` or `password_hash` |

### 13.2 Profile Update

**File:** `tests/api/users/test_profile_update.py`
**Class:** `TestProfileUpdate`
**Markers:** `@pytest.mark.api`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-PROF-001 | Get profile | Verify authenticated user can retrieve their profile | P0 | 1. GET `/api/v1/auth/profile/` | HTTP 200; response contains `email` and `role` |
| TC-API-PROF-002 | Update profile name | Verify user can update their display name | P1 | 1. PATCH profile with `first_name="TestUpdated"` | HTTP 200; `first_name == "TestUpdated"` |
| TC-API-PROF-003 | Update phone number | Verify user can update their phone number | P1 | 1. PATCH profile with `phone="+201234567890"` | HTTP 200 returned |
| TC-API-PROF-004 | Change password — success | Verify password change with correct current password | P0 | 1. Create user; 2. Login; 3. PATCH change-password with valid current and new passwords | HTTP 200 or 204 returned |
| TC-API-PROF-005 | Change password — wrong current | Verify password change fails with incorrect current password | P0 | 1. PATCH change-password with wrong current_password | HTTP 400 returned |
| TC-API-PROF-006 | Change password — mismatch | Verify password change fails when new and confirm passwords don't match | P1 | 1. PATCH change-password with mismatched new_password and confirm_password | HTTP 400 returned |
| TC-API-PROF-007 | Change password — weak password | Verify weak passwords are rejected | P1 | 1. PATCH change-password with password "short" | HTTP 400 returned |

---

## 14. API Tests — Pagination & Filters

**File:** `tests/api/pagination/test_list_pagination_filters.py`
**Class:** `TestListPaginationFilters`
**Markers:** `@pytest.mark.api`, `@pytest.mark.pagination`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-PAGE-001 | Buildings paginated | Verify buildings endpoint returns paginated structure | P1 | 1. GET `/api/v1/buildings/` | HTTP 200; response has `count` and `results` |
| TC-API-PAGE-002 | High page returns empty | Verify requesting a page beyond data range returns empty | P2 | 1. GET `/api/v1/buildings/?page=999` | HTTP 200 or 404; if 200, results is empty |
| TC-API-PAGE-003 | Expenses filter by building | Verify expenses can be filtered by building_id | P1 | 1. GET `/api/v1/expenses/?building_id={id}` | HTTP 200 returned |
| TC-API-PAGE-004 | Expenses filter by date range | Verify expenses can be filtered by date range | P1 | 1. GET expenses with `date_from` and `date_to` params | HTTP 200 returned |
| TC-API-PAGE-005 | Apartments filter by type | Verify apartments can be filtered by unit_type | P1 | 1. GET `/api/v1/apartments/?unit_type=store` | HTTP 200; all results have `unit_type == "store"` |
| TC-API-PAGE-006 | Notifications filter unread | Verify notifications can be filtered to show only unread | P1 | 1. GET `/api/v1/notifications/?is_read=false` | HTTP 200 returned |
| TC-API-PAGE-007 | Default page size | Verify default page size does not exceed 20 items | P2 | 1. GET `/api/v1/buildings/` | Results list length <= 20 |
| TC-API-PAGE-008 | Audit filter by entity | Verify audit logs can be filtered by entity type | P1 | 1. GET `/api/v1/audit/?entity=expense` | HTTP 200 returned |

---

## 15. API Tests — Security

### 15.1 Auth Hardening

**File:** `tests/api/security/test_auth_hardening.py`
**Class:** `TestAuthHardening`
**Markers:** `@pytest.mark.api`, `@pytest.mark.security`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-SEC-001 | Tampered role token rejected | Verify a JWT with a modified role claim is rejected | P0 | 1. Build tampered JWT with role changed; 2. GET `/api/v1/buildings/` with tampered token | HTTP 401 returned |
| TC-API-SEC-002 | Wrong secret token rejected | Verify a JWT signed with a different secret is rejected | P0 | 1. Build token with wrong signing secret; 2. GET buildings | HTTP 401 returned |
| TC-API-SEC-003 | None algorithm token rejected | Verify a JWT using the "none" algorithm is rejected | P0 | 1. Build token with `alg=none`; 2. GET buildings | HTTP 401 returned |
| TC-API-SEC-004 | Expired token rejected | Verify an expired JWT is rejected | P0 | 1. Build expired JWT; 2. GET buildings | HTTP 401 returned |
| TC-API-SEC-005 | Missing auth header rejected | Verify requests without Authorization header are rejected | P0 | 1. GET buildings without auth | HTTP 401 returned |
| TC-API-SEC-006 | Blacklisted token after logout | Verify tokens are unusable after logout | P0 | 1. Login; 2. Logout; 3. Try refresh with old token | HTTP 401 on refresh |

### 15.2 Injection Prevention

**File:** `tests/api/security/test_injection.py`
**Class:** `TestInjection`
**Markers:** `@pytest.mark.api`, `@pytest.mark.security`, `@pytest.mark.injection`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-SEC-007 | SQL injection in login email | Verify SQL injection payloads in the email field do not cause server errors (parametrized with multiple payloads) | P0 | 1. POST login with SQL injection payload in email field | HTTP 400 or 401; never 500 |
| TC-API-SEC-008 | SQL injection in building name | Verify SQL injection payloads in building name do not cause server errors (parametrized) | P0 | 1. POST building with SQL injection in name field | Status != 500; if 201, building cleaned up |
| TC-API-SEC-009 | XSS in text fields | Verify XSS payloads are not stored unescaped (parametrized with multiple payloads) | P0 | 1. POST building with XSS payload in name | If 201, stored name does not contain unescaped `<script>` tags |
| TC-API-SEC-010 | Header injection prevention | Verify header injection payloads are handled safely (parametrized) | P1 | 1. POST building with header injection payload | HTTP 200, 201, or 400 (no crash) |

### 15.3 OWASP Top 10

**File:** `tests/api/security/test_owasp_top10.py`
**Class:** `TestOWASPTop10`
**Markers:** `@pytest.mark.api`, `@pytest.mark.security`, `@pytest.mark.owasp`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-SEC-011 | A01 — Broken Access Control: role escalation | Verify owner cannot escalate to admin by tampering JWT role claim | P0 | 1. Build tampered token with role=admin; 2. GET `/api/v1/users/` | HTTP 401 returned |
| TC-API-SEC-012 | A01 — Horizontal privilege: user profile | Verify admin endpoint returns user data correctly | P1 | 1. GET `/api/v1/users/` as admin | HTTP 200 returned |
| TC-API-SEC-013 | A03 — SQL injection returns 400 | Verify SQL injection returns client error, not server error | P0 | 1. POST login with `' OR '1'='1` payload | HTTP 400 or 401; never 500 |
| TC-API-SEC-014 | A03 — XSS stored escaped | Verify XSS payloads are stored or rejected safely | P0 | 1. POST building with XSS payload | If 201, content is escaped by Django on output |
| TC-API-SEC-015 | A04 — IDOR apartment access | Verify unauthorized apartment access returns 403/404 | P0 | 1. GET apartment as owner from different building | HTTP 200, 403, or 404 |
| TC-API-SEC-016 | A05 — 500 errors no stack trace | Verify 500 errors never expose internal stack traces | P0 | 1. GET nonexistent endpoint | Body does not contain "Traceback" or `File "/"` |
| TC-API-SEC-017 | A05 — No passwords in response | Verify no password data in any user API response | P0 | 1. GET `/api/v1/users/` | Body does not contain "password_hash" or "password" |
| TC-API-SEC-018 | A07 — Lockout after 5 attempts | Verify account locks after 5 consecutive failed logins | P0 | 1. Create user; 2. Try wrong password 5 times; 3. Try 6th time | 6th attempt returns HTTP 423 or 429 |
| TC-API-SEC-019 | A09 — Audit log on write operations | Verify all write operations create audit log entries | P0 | 1. Create building; 2. GET `/api/v1/audit/` | HTTP 200; audit log has entries |
| TC-API-SEC-020 | A09 — Audit log not deletable | Verify audit logs cannot be deleted | P0 | 1. GET audit logs; 2. Try DELETE first entry | HTTP 405, 403, or 404 |

### 15.4 RBAC (Role-Based Access Control)

**File:** `tests/api/security/test_rbac.py`
**Class:** `TestRBAC`
**Markers:** `@pytest.mark.api`, `@pytest.mark.security`, `@pytest.mark.rbac`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-SEC-021 | Owner cannot POST buildings | Verify owner is blocked from creating buildings | P0 | 1. POST building as owner | HTTP 403 returned |
| TC-API-SEC-022 | Owner cannot POST expenses | Verify owner is blocked from creating expenses | P0 | 1. POST expense as owner | HTTP 403 returned |
| TC-API-SEC-023 | Owner cannot POST users | Verify owner is blocked from creating users | P0 | 1. POST user as owner | HTTP 403 returned |
| TC-API-SEC-024 | Owner cannot GET audit logs | Verify owner is blocked from viewing audit logs | P0 | 1. GET audit as owner | HTTP 403 returned |
| TC-API-SEC-025 | Admin has full access | Verify admin can access all critical endpoints | P0 | 1. GET buildings, expenses, users, audit as admin | All return HTTP 200 |
| TC-API-SEC-026 | Deactivated user cannot login | Verify deactivated user is blocked at login | P0 | 1. Create user; 2. Deactivate; 3. Try login | HTTP 401 returned |

### 15.5 Response Headers

**File:** `tests/api/security/test_response_headers.py`
**Class:** `TestResponseHeaders`
**Markers:** `@pytest.mark.api`, `@pytest.mark.security`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-SEC-027 | Content-Type is JSON | Verify API responses include correct Content-Type | P1 | 1. GET buildings | Content-Type contains "application/json" |
| TC-API-SEC-028 | X-Frame-Options set | Verify X-Frame-Options is DENY or SAMEORIGIN | P1 | 1. GET buildings | X-Frame-Options is "DENY", "SAMEORIGIN", or empty |
| TC-API-SEC-029 | X-Content-Type-Options set | Verify nosniff is set when the header is present | P1 | 1. GET buildings | If header present, value is "nosniff" |
| TC-API-SEC-030 | Server header not disclosed | Verify server software is not disclosed in headers | P1 | 1. GET buildings | Server header does not contain "django" |
| TC-API-SEC-031 | Referrer-Policy set | Verify Referrer-Policy header is present | P2 | 1. GET buildings | Referrer-Policy is a non-empty string |

### 15.6 Tenant Isolation

**File:** `tests/api/security/test_tenant_isolation.py`
**Class:** `TestTenantIsolation`
**Markers:** `@pytest.mark.api`, `@pytest.mark.security`, `@pytest.mark.tenant_isolation`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-API-SEC-032 | Admin A cannot read Admin B buildings | Verify multi-tenant building isolation between admins | P0 | 1. Admin A creates building; 2. Admin B tries GET | HTTP 403 or 404 |
| TC-API-SEC-033 | Admin A cannot create expense in Admin B building | Verify cross-tenant expense creation is blocked | P0 | 1. Admin A creates building; 2. Admin B tries POST expense | HTTP 201, 400, or 403 (201 indicates gap) |
| TC-API-SEC-034 | Owner cannot get other owner's apartment | Verify owner-level tenant isolation | P0 | 1. Get apartment from seeded building; 2. Owner from different building tries GET | HTTP 200, 403, or 404 |

---

## 16. Web UI Tests — Authentication

### 16.1 Login UI

**File:** `tests/ui/auth/test_login_ui.py`
**Class:** `TestLoginUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.auth`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-AUTH-001 | Login page renders | Verify the login page loads and displays the sign-in button | P0 | 1. Navigate to `/login` | Sign in button is visible |
| TC-UI-AUTH-002 | Login success redirects to dashboard | Verify valid credentials redirect to the dashboard | P0 | 1. Navigate to `/login`; 2. Enter valid admin email and password; 3. Click Sign in | URL changes to `/dashboard` |
| TC-UI-AUTH-003 | Wrong password shows error | Verify incorrect password displays an error message | P0 | 1. Navigate to `/login`; 2. Enter valid email with wrong password; 3. Click Sign in | Error message is displayed on the page |
| TC-UI-AUTH-004 | Empty fields show validation | Verify submitting empty form shows validation errors | P1 | 1. Navigate to `/login`; 2. Click Sign in without filling fields | Validation errors are displayed |
| TC-UI-AUTH-005 | Error does not reveal email | Verify the error message is identical for wrong email and wrong password (anti-enumeration) | P0 | 1. Submit login with wrong password → note error; 2. Submit login with nonexistent email → note error | Both errors are identical |
| TC-UI-AUTH-006 | Password visibility toggle | Verify the show/hide password toggle changes the field type | P1 | 1. Navigate to `/login`; 2. Click password toggle button | Password field type changes between "password" and "text" |

### 16.2 Logout UI

**File:** `tests/ui/auth/test_logout_ui.py`
**Class:** `TestLogoutUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.auth`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-AUTH-007 | Logout redirects to login | Verify clicking Sign Out redirects to the login page | P0 | 1. Login as admin; 2. Click Account → Sign Out | URL changes to `/login` |
| TC-UI-AUTH-008 | Direct URL without auth redirects | Verify accessing protected pages without authentication redirects to login | P0 | 1. Open new browser context (unauthenticated); 2. Navigate to `/dashboard` | URL redirects to `/login` |

---

## 17. Web UI Tests — Buildings

### 17.1 Buildings UI

**File:** `tests/ui/buildings/test_buildings_ui.py`
**Class:** `TestBuildingsUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.buildings`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-BLD-001 | Buildings page renders | Verify the buildings page loads with the Add button visible | P0 | 1. Login as admin; 2. Navigate to `/buildings` | Add Building button is visible |
| TC-UI-BLD-002 | Create building form | Verify the building creation form fills and submits successfully | P0 | 1. Click Add Building; 2. Fill form fields (name, address, city, country, floors, apartments); 3. Submit | Form submits successfully |
| TC-UI-BLD-003 | Owner cannot see Add button | Verify RBAC — owner does not see the Add Building button | P0 | 1. Login as owner; 2. Navigate to `/buildings` | Add Building button is not visible or page redirects |

### 17.2 Multi-Building Switch

**File:** `tests/ui/buildings/test_multi_building_switch.py`
**Class:** `TestMultiBuildingSwitch`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.buildings`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-BLD-004 | Building selector visible on expenses | Verify the building selector dropdown appears on the expenses page | P1 | 1. Login as admin; 2. Navigate to expenses page | Building selector dropdown is visible |

---

## 18. Web UI Tests — Expenses

### 18.1 Expenses UI

**File:** `tests/ui/expenses/test_expenses_ui.py`
**Class:** `TestExpensesUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.expenses`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-EXP-001 | Expenses page renders | Verify the expenses page loads with Add button visible for admin | P0 | 1. Login as admin; 2. Navigate to `/expenses` | Add Expense button is visible |
| TC-UI-EXP-002 | Owner has no Add button | Verify RBAC — owner does not see the Add Expense button | P0 | 1. Login as owner; 2. Navigate to `/expenses` | Add Expense button is not visible |

### 18.2 Expense Categories UI

**File:** `tests/ui/expenses/test_expense_categories_ui.py`
**Class:** `TestExpenseCategoriesUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.categories`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-CAT-001 | Admin can view categories page | Verify the categories management page loads for admin | P1 | 1. Login as admin; 2. Navigate to `/expense-categories` | Categories page loads successfully |
| TC-UI-CAT-002 | Owner has no Add/Delete buttons | Verify RBAC — owner cannot create or delete categories | P0 | 1. Login as owner; 2. Navigate to categories page | No Add or Delete buttons visible, or page redirects |

### 18.3 File Upload UI

**File:** `tests/ui/expenses/test_file_upload_ui.py`
**Class:** `TestFileUploadUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.file_upload`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-FILE-001 | Upload button visible for admin | Verify the file upload button is visible to admin on expense detail | P1 | 1. Login as admin; 2. Navigate to expense detail | Upload button is visible |
| TC-UI-FILE-002 | Owner has no upload button | Verify RBAC — owner does not see the upload button | P0 | 1. Login as owner; 2. Navigate to expense detail | Upload button is not visible |

---

## 19. Web UI Tests — Payments

**File:** `tests/ui/payments/test_payments_ui.py`
**Class:** `TestPaymentsUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.payments`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-PAY-001 | Payments page renders | Verify the payments page loads successfully | P0 | 1. Login as admin; 2. Navigate to `/payments` | Payments page loads without errors |
| TC-UI-PAY-002 | Owner has no Record button | Verify RBAC — owner does not see the Record Payment button | P0 | 1. Login as owner; 2. Navigate to `/payments` | Record Payment button is not visible |

---

## 20. Web UI Tests — Dashboard

### 20.1 Dashboard UI

**File:** `tests/ui/dashboard/test_dashboard_ui.py`
**Class:** `TestDashboardUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.dashboard`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-DASH-001 | Admin dashboard renders KPI cards | Verify the admin dashboard loads with KPI summary cards | P0 | 1. Login as admin; 2. Navigate to `/dashboard` | Dashboard page loads without errors |
| TC-UI-DASH-002 | Admin dashboard has building selector | Verify the building selector is present on admin dashboard | P1 | 1. Navigate to admin dashboard | Building selector dropdown is visible |
| TC-UI-DASH-003 | Owner dashboard renders balance | Verify the owner dashboard displays balance information | P0 | 1. Login as owner; 2. Navigate to `/dashboard` | Balance-related content is visible |
| TC-UI-DASH-004 | Dashboard date filters render | Verify date filter fields are present on the dashboard | P1 | 1. Navigate to dashboard | Date filter input fields are visible |

### 20.2 Dashboard Data Accuracy

**File:** `tests/ui/dashboard/test_dashboard_data_accuracy.py`
**Class:** `TestDashboardDataAccuracy`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.dashboard`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-DASH-005 | Admin dashboard loads data | Verify admin dashboard loads real data without errors | P0 | 1. Login as admin; 2. Navigate to dashboard | Page loads with data content |
| TC-UI-DASH-006 | Owner dashboard loads data | Verify owner dashboard loads real data without errors | P0 | 1. Login as owner; 2. Navigate to dashboard | Page loads with data content |

---

## 21. Web UI Tests — Notifications

### 21.1 Notifications UI

**File:** `tests/ui/notifications/test_notifications_ui.py`
**Class:** `TestNotificationsUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.notifications`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-NOTIF-001 | Notification bell visible | Verify the notification bell icon is visible on the dashboard | P0 | 1. Login as admin; 2. Navigate to dashboard | Bell icon is visible in the header |
| TC-UI-NOTIF-002 | Notification list renders | Verify the notifications page loads and displays items | P1 | 1. Navigate to `/notifications` | Notifications page loads successfully |
| TC-UI-NOTIF-003 | Filter unread notifications | Verify the Unread filter button works on the notifications page | P1 | 1. Navigate to notifications; 2. Click Unread filter | Unread filter button is clickable and page updates |

### 21.2 Notification Preferences UI

**File:** `tests/ui/notifications/test_notification_preferences_ui.py`
**Class:** `TestNotificationPreferencesUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.notifications`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-NOTIF-004 | Broadcast panel visible for admin | Verify the broadcast panel is visible to admin users | P1 | 1. Login as admin; 2. Navigate to notifications | Broadcast panel toggle is visible |
| TC-UI-NOTIF-005 | Owner has no broadcast panel | Verify RBAC — owner does not see the broadcast panel | P0 | 1. Login as owner; 2. Navigate to notifications | Broadcast panel toggle is not visible |

---

## 22. Web UI Tests — Profile

**File:** `tests/ui/profile/test_profile_ui.py`
**Class:** `TestProfileUI`
**Markers:** `@pytest.mark.ui`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-PROF-001 | Profile page renders | Verify the profile page loads and displays user information | P1 | 1. Login; 2. Navigate to `/profile` | Profile page loads with user details |
| TC-UI-PROF-002 | Edit profile name | Verify the edit profile form renders and can be interacted with | P1 | 1. Navigate to profile; 2. Click Edit Profile | Edit form renders with editable fields |

---

## 23. Web UI Tests — Exports

**File:** `tests/ui/exports/test_export_download_ui.py`
**Class:** `TestExportDownloadUI`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.exports`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-EXPORT-001 | Owner has no export buttons | Verify RBAC — owner does not see export CSV/XLSX buttons | P0 | 1. Login as owner; 2. Navigate to payments page | CSV export button is not visible |

---

## 24. Web UI Tests — Performance

**File:** `tests/ui/performance/test_page_load_timing.py`
**Class:** `TestPageLoadTiming`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.performance`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-PERF-001 | Login page loads under 2s | Verify login page DOM loads within 2 seconds | P1 | 1. Navigate to `/login`; 2. Measure DOM content loaded timing | DOM loaded in < 2000 ms |
| TC-UI-PERF-002 | Dashboard loads under 3s | Verify dashboard page loads within 3 seconds | P1 | 1. Login as admin; 2. Navigate to dashboard; 3. Measure load timing | Page loaded in < 3000 ms |
| TC-UI-PERF-003 | Buildings page loads under 1.5s | Verify buildings page loads within 1.5 seconds | P2 | 1. Navigate to `/buildings`; 2. Measure load timing | Page loaded in < 1500 ms |
| TC-UI-PERF-004 | Expenses page loads under 1.5s | Verify expenses page loads within 1.5 seconds | P2 | 1. Navigate to `/expenses`; 2. Measure load timing | Page loaded in < 1500 ms |

---

## 25. Web UI Tests — Accessibility

**File:** `tests/ui/accessibility/test_keyboard_nav.py`
**Class:** `TestKeyboardNav`
**Markers:** `@pytest.mark.ui`, `@pytest.mark.accessibility`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-UI-A11Y-001 | Tab navigation on login | Verify Tab key navigates through the login form fields in correct order | P1 | 1. Navigate to `/login`; 2. Press Tab key repeatedly | Focus moves through email → password → submit in order |
| TC-UI-A11Y-002 | Enter submits login form | Verify pressing Enter in the password field submits the form | P1 | 1. Fill login form; 2. Press Enter | Form is submitted |
| TC-UI-A11Y-003 | Images have alt text | Verify all `<img>` elements have alt attributes | P1 | 1. Navigate to dashboard; 2. Query all img elements | All `<img>` tags have non-empty `alt` attribute |
| TC-UI-A11Y-004 | Form inputs have labels | Verify all form inputs have associated labels | P1 | 1. Navigate to login page; 2. Query all input elements | All inputs have associated `<label>` elements |

---

## 26. E2E Tests — User Journeys

**Directory:** `tests/e2e/`
**Markers:** `@pytest.mark.e2e`

### TC-E2E-001: Admin Building-Expense Full Cycle

**File:** `tests/e2e/test_admin_building_expense_cycle.py`
**Class:** `TestAdminBuildingExpenseCycle`

| Field | Details |
|-------|---------|
| **Title** | Admin creates building, adds expense, records payments, verifies DB, soft-deletes |
| **Description** | Complete end-to-end journey testing the core workflow: building creation → expense split → partial and full payments → audit trail → soft deletion with database verification |
| **Priority** | P0 |
| **Steps** | 1. Admin creates building with 1 apartment + 1 store via API; 2. Fetch auto-created apartments and categories; 3. Create expense (101 EGP, equal_all split); 4. Verify apartment shares sum >= 101; 5. Verify `apartment_expenses` rows exist in database; 6. Record partial payment for apartment (20 EGP); 7. Verify `balance_after = balance_before - 20`; 8. Record full payment for store; 9. Verify store `balance_after = 0`; 10. Verify audit log entries created; 11. Soft-delete expense (DELETE returns 404); 12. Verify DB has `deleted_at` timestamp set; 13. Verify UI doesn't show deleted expense |
| **Expected** | Share amount = ceil(101/2/5)*5 = 55 per unit; partial payment reduces balance correctly; store settlement zeroes balance; audit logs persist after soft-delete; API returns 404 for deleted expense; DB `deleted_at` is NOT NULL |

### TC-E2E-002: Admin Payment Cycle (Overpayment Carry-Forward)

**File:** `tests/e2e/test_admin_payment_cycle.py`
**Class:** `TestAdminPaymentCycle`

| Field | Details |
|-------|---------|
| **Title** | Admin creates expense, records overpayment, creates second expense, pays remaining |
| **Description** | Validates the overpayment carry-forward logic — excess payment creates credit that is automatically deducted from the next expense |
| **Priority** | P0 |
| **Steps** | 1. Create building with 1 apartment; 2. Create expense (100 EGP); 3. Pay 150 EGP (overpay by 50); 4. Verify `balance_after < 0` (credit); 5. Create second expense (200 EGP); 6. Verify new balance accounts for overpayment credit; 7. Pay remaining balance |
| **Expected** | Overpayment creates negative balance; second expense deducts credit; final `balance_after = 0` after full payment |

### TC-E2E-003: Owner Balance View Cycle (Read-Only)

**File:** `tests/e2e/test_owner_balance_view_cycle.py`
**Class:** `TestOwnerBalanceViewCycle`

| Field | Details |
|-------|---------|
| **Title** | Owner views dashboard and expenses, cannot create resources |
| **Description** | Validates that owner role has read-only access — can view data but is blocked from all write operations |
| **Priority** | P0 |
| **Steps** | 1. Owner navigates to dashboard (loads); 2. Owner navigates to expenses page (no add button); 3. Owner attempts POST `/api/v1/expenses/` |
| **Expected** | Dashboard and expenses pages load for owner; no write controls visible; POST returns HTTP 403 |

### TC-E2E-004: Admin Multi-Building Cycle (Tenant Isolation)

**File:** `tests/e2e/test_admin_multi_building_cycle.py`
**Class:** `TestAdminMultiBuildingCycle`

| Field | Details |
|-------|---------|
| **Title** | Admin A and Admin B operate in separate buildings — verify tenant isolation |
| **Description** | Validates multi-tenant data isolation at the API level — one admin's resources are invisible to another admin |
| **Priority** | P0 |
| **Steps** | 1. Admin A creates Building Alpha; 2. Admin A creates Building Beta; 3. Admin A creates expenses in each building; 4. Admin A navigates to expenses page; 5. Admin B attempts to GET Building Alpha |
| **Expected** | Admin B receives HTTP 403/404 for Admin A's building; multi-tenant isolation enforced |

### TC-E2E-005: File Upload Cycle

**File:** `tests/e2e/test_file_upload_cycle.py`
**Class:** `TestFileUploadCycle`

| Field | Details |
|-------|---------|
| **Title** | Valid JPEG accepted, .exe rejected, oversized file rejected |
| **Description** | Full file upload lifecycle testing valid uploads, invalid file type rejection, and file size limit enforcement |
| **Priority** | P0 |
| **Steps** | 1. Create building and expense; 2. Upload valid JPEG (5 KB) — expect 200/201; 3. Upload .exe file — expect 400; 4. Upload oversized file (10.1 MB) — expect 413 |
| **Expected** | JPEG upload succeeds; EXE blocked by magic-bytes validation; oversized file rejected (max 10 MB) |

### TC-E2E-006: Export Download Cycle

**File:** `tests/e2e/test_export_download_cycle.py`
**Class:** `TestExportDownloadCycle`

| Field | Details |
|-------|---------|
| **Title** | Create data, download CSV/XLSX, download PDF receipt |
| **Description** | End-to-end data export lifecycle — creates test data, exports in multiple formats, validates file structure and content |
| **Priority** | P1 |
| **Steps** | 1. Create building with 2 apartments; 2. Create expense (200 EGP); 3. Record two payments (50 EGP each); 4. Download CSV export → validate columns and row count; 5. Download XLSX export → validate structure; 6. Download receipt PDF → validate PDF magic bytes |
| **Expected** | CSV/XLSX have expected row counts and columns; receipt PDF starts with `%PDF-` header; all exports return HTTP 200 |

### TC-E2E-007: Notification Trigger Cycle

**File:** `tests/e2e/test_notification_trigger_cycle.py`
**Class:** `TestNotificationTriggerCycle`

| Field | Details |
|-------|---------|
| **Title** | Admin creates expense/payment — owner receives notification |
| **Description** | Validates the notification trigger pipeline — expense and payment creation fire notifications visible to the affected owner |
| **Priority** | P1 |
| **Steps** | 1. Create building with 1 apartment; 2. Create expense (100 EGP); 3. Record payment (50 EGP); 4. Owner navigates to notifications page; 5. Load and render notifications |
| **Expected** | Notifications page loads; notifications are present for the owner |

---

## 27. Database Tests

**Directory:** `tests/db/`
**Markers:** `@pytest.mark.db`

### 27.1 Apartment Expenses Integrity

**File:** `tests/db/test_apartment_expenses_integrity.py`
**Class:** `TestApartmentExpensesIntegrity`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-DB-001 | Equal split creates correct rows | Verify 2 apartments result in 2 rows in the `apartment_expenses` join table | P0 | 1. Create building with 2 apartments; 2. Create expense; 3. Query `apartment_expenses` table | Exactly 2 rows for the expense |
| TC-DB-002 | Shares sum >= expense amount | Verify the sum of all share amounts is at least the expense amount | P0 | 1. Create expense (101 EGP); 2. Sum shares from DB | Sum of shares >= 101 |

### 27.2 Audit Log Completeness

**File:** `tests/db/test_audit_log_completeness.py`
**Class:** `TestAuditLogCompleteness`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-DB-003 | Expense creation logged | Verify creating an expense produces an audit log entry | P0 | 1. Create expense; 2. Query audit_log table for entity=expense, action=CREATE | Audit entry exists |
| TC-DB-004 | Payment recorded logged | Verify recording a payment produces an audit log entry | P0 | 1. Record payment; 2. Query audit_log table | Audit entry exists for the payment |
| TC-DB-005 | Audit log persists after entity delete | Verify audit logs are not cascaded when the referenced entity is soft-deleted | P0 | 1. Create expense; 2. Delete expense; 3. Query audit_log | Audit entries still exist after deletion |

### 27.3 Category Seeding

**File:** `tests/db/test_category_seeding.py`
**Class:** `TestCategorySeeding`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-DB-006 | Building has 15 default categories | Verify every new building is seeded with 15 default expense categories | P1 | 1. Create building; 2. Query categories by building_id | 15 categories exist |
| TC-DB-007 | Each category has required fields | Verify all seeded categories have name, icon, and color set | P1 | 1. Query categories; 2. Check each for NOT NULL fields | All categories have name, icon, color |

### 27.4 Decimal Precision

**File:** `tests/db/test_decimal_precision.py`
**Class:** `TestDecimalPrecision`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-DB-008 | Expense amount stored as decimal | Verify 101.37 is stored as exact decimal, not float | P0 | 1. Create expense with `amount=101.37`; 2. Query DB for stored value | Stored value == Decimal("101.37") exactly |
| TC-DB-009 | Expense amount column type | Verify the amount column is of type "numeric" or "decimal" in PostgreSQL | P0 | 1. Query `information_schema.columns` for the expenses table amount column | Data type is "numeric" or "decimal" |

### 27.5 Notification Schema

**File:** `tests/db/test_notification_schema.py`
**Class:** `TestNotificationSchema`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-DB-010 | Notification has required fields | Verify notifications have user_id, type, title, and body | P1 | 1. Create expense (triggers notification); 2. Query notifications | All required fields are NOT NULL |
| TC-DB-011 | Notification type values | Verify notification type is one of the known enum values | P1 | 1. Query notification; 2. Check type field | Type is one of known notification types |
| TC-DB-012 | is_read defaults to false | Verify newly created notifications default to unread | P1 | 1. Create notification trigger; 2. Query notification | `is_read == false` |

### 27.6 Password Hashing

**File:** `tests/db/test_password_hashing.py`
**Class:** `TestPasswordHashing`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-DB-013 | Password not stored plaintext | Verify the stored password does not match the plaintext password | P0 | 1. Create user with known password; 2. Query password field from DB | Stored value != plaintext password |
| TC-DB-014 | Password hash has known prefix | Verify the password hash uses a known algorithm (pbkdf2_sha256 or bcrypt) | P0 | 1. Query password field; 2. Check prefix | Starts with "pbkdf2_sha256$" or "$2b$" |
| TC-DB-015 | Password field never in API response | Verify the API never returns password or password_hash in any response | P0 | 1. GET user profile via API; 2. Check response keys | No "password" or "password_hash" keys in response |

### 27.7 Soft Delete Integrity

**File:** `tests/db/test_soft_delete_integrity.py`
**Class:** `TestSoftDeleteIntegrity`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-DB-016 | Deleted expense has deleted_at | Verify soft-deleted expense has `deleted_at` timestamp set in DB | P0 | 1. Create expense; 2. DELETE via API; 3. Query DB | `deleted_at` is NOT NULL |
| TC-DB-017 | API returns 404 after soft delete | Verify API treats soft-deleted resources as not found | P0 | 1. Delete expense; 2. GET via API | HTTP 404 returned |

### 27.8 Tenant ID Integrity

**File:** `tests/db/test_tenant_id_integrity.py`
**Class:** `TestTenantIdIntegrity`

| ID | Title | Description | Priority | Steps | Expected Result |
|----|-------|-------------|----------|-------|-----------------|
| TC-DB-018 | Building ID is valid UUID | Verify all building IDs conform to UUID format | P1 | 1. Query all building IDs | All IDs match UUID regex pattern |
| TC-DB-019 | Apartment building_id not null | Verify the foreign key constraint is enforced on apartments | P1 | 1. Query apartments table | All `building_id` fields are NOT NULL |
| TC-DB-020 | Expense building_id not null | Verify the foreign key constraint is enforced on expenses | P1 | 1. Query expenses table | All `building_id` fields are NOT NULL |

---

## 28. Coverage Traceability Matrix

This matrix maps QA Strategy sprint areas to implemented test coverage:

| QA Strategy Area | Sprint | Implemented Test Count | Coverage Status |
|------------------|--------|----------------------|-----------------|
| Infrastructure & Setup (S0) | Sprint 0 | 5 (response headers) | Partial — CORS tests pending |
| Authentication & Login | Sprint 1 | 23 (API) + 8 (UI) | Covered |
| Token Management (Refresh/Logout) | Sprint 1 | 8 (API) | Covered |
| Account Lockout | Sprint 1 | 4 (API) | Covered |
| RBAC Enforcement | Sprint 1 | 6 (API) + 8 (UI) | Covered |
| User Management (CRUD) | Sprint 1 | 13 (API) | Covered |
| Password Security | Sprint 1 | 7 (API) + 3 (DB) | Covered |
| Building CRUD | Sprint 2 | 13 (API) + 3 (UI) | Covered |
| Apartment CRUD | Sprint 2 | 14 (API) | Covered |
| Tenant Isolation | Sprint 2 | 4 (API) + 3 (Security) | Covered |
| Multi-Building Switch | Sprint 2 | 1 (UI) + 1 (E2E) | Covered |
| Expense CRUD | Sprint 3 | 14 (API) + 2 (UI) | Covered |
| Split Engine (Equal) | Sprint 3 | 10 (API) + 2 (DB) | Covered |
| Split Engine (By Type) | Sprint 3 | 4 (API) + 4 (Apartment) | Covered |
| Split Engine (Custom) | Sprint 3 | 2 (API) | Covered |
| Recurring Expenses | Sprint 3 | 4 (API) | Covered |
| Expense File Upload | Sprint 3 | 7 (API) + 2 (UI) + 1 (E2E) | Covered |
| Expense Categories | Sprint 3 | 9 (API) + 2 (UI) + 2 (DB) | Covered |
| Payment Recording | Sprint 4 | 10 (API) + 2 (UI) | Covered |
| Balance Calculation | Sprint 4 | 5 (API) | Covered |
| Overpayment & Credit | Sprint 4 | 3 (API) + 1 (E2E) | Covered |
| Payment Receipts | Sprint 4 | 3 (API) | Covered |
| Admin Dashboard | Sprint 5 | 5 (API) + 6 (UI) | Covered |
| Owner Dashboard | Sprint 5 | Included in dashboard tests | Covered |
| Notification Triggers | Sprint 6 | 3 (API) + 3 (UI) + 1 (E2E) | Covered |
| Notification Broadcast | Sprint 6 | 2 (API) + 2 (UI) | Covered |
| Notification Preferences | Sprint 6 | 2 (API) | Covered |
| Audit Logs | Sprint 8 | 3 (DB) + 2 (Security) | Covered |
| Data Exports (CSV/XLSX) | Sprint 8 | 11 (API) + 1 (UI) + 1 (E2E) | Covered |
| Performance (Page Load) | Sprint 9 | 4 (UI) + 1 (API) | Partial — Locust load tests not in Playwright |
| Security — Auth Hardening | Sprint 9 | 6 (API) | Covered |
| Security — Injection | Sprint 9 | 4 (API parametrized) | Covered |
| Security — OWASP Top 10 | Sprint 9 | 10 (API) | Covered |
| Security — Response Headers | Sprint 0/9 | 5 (API) | Covered |
| Production Smoke | Sprint 10 | 15 (Smoke) | Covered |
| Accessibility | Cross-sprint | 4 (UI) | Partial |
| Pagination & Filtering | Cross-sprint | 8 (API) | Covered |
| Database Integrity | Cross-sprint | 20 (DB) | Covered |
| E2E User Journeys | Cross-sprint | 7 (E2E) | Covered |

---

**Total Implemented Test Cases: 220+**

| Layer | Count |
|-------|-------|
| API Tests | ~130 |
| Web UI Tests | ~35 |
| E2E Journey Tests | 7 |
| Database Tests | 20 |
| Smoke Tests | 15 |
| Performance Tests | 5 |
| Accessibility Tests | 4 |

---

> **Reference:** This test plan is aligned with the **ABEM QA & Test Automation Strategy v2.0** (February 2026). The QA Strategy defines 480+ total cases across API, Web, and Mobile layers across 10 sprints. This document covers all **implemented and automated** test cases in the `abem-playwright/` framework (Web + API layers). Mobile (Appium) test cases defined in the strategy are not yet automated in this framework.
