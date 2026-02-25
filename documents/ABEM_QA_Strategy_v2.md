# ABEM

Apartment & Building Expense Management

# QA & TEST AUTOMATION STRATEGY

*Complete Test Coverage — All 10 Sprints*

**Web · API · Mobile**

Version 2.0 | February 2026

| Attribute | Detail |
|---|---|
| Document Type | QA Strategy & Master Test Plan |
| Framework | pytest · Selenium 4 · Appium 3 |
| Language | Python 3.12 |
| Scope | Sprint 0 through Sprint 10 (all sprints) |
| Total Test Cases | 480+ across API, Web UI & Mobile |
| CI Integration | GitHub Actions — auto on every push |

---

## 1. QA Strategy Overview

Quality is built into every sprint. Tests are written alongside the feature in the same sprint cycle, not after. As the embedded senior automation QA engineer, the framework follows three core principles:

- Shift Left: Tests are specified before implementation starts — acceptance criteria drive test cases.
- Risk-Based: Financial calculations, RBAC, and tenant data isolation are highest priority. A bug in the payment split engine or a RBAC bypass affects real money across all tenants.
- Full-Stack: Every feature is verified independently at API, Web UI, and Mobile layers. A bug cannot hide in one layer while passing another.

### 1.1 Test Layer Strategy

| Layer | Tool | What It Validates | Trigger |
|---|---|---|---|
| API | pytest + requests | Business logic, auth, RBAC, data integrity, security | Every commit to any branch |
| Web UI | Selenium 4 + POM pattern | User flows, rendering, form validation, accessibility | Every commit |
| Mobile | Appium 3 (Flutter / Dart) | Role-based UI, device APIs, secure storage, UX | Every pull request |
| Performance | Locust 2.x | P95 response times, concurrent user load | Nightly + pre-release |
| Security | pytest + PyJWT + custom | OWASP Top 10, injection, CORS, headers | Every sprint |

### 1.2 Test ID Convention

Every test case follows a consistent ID format used in pytest markers, reports, and this document:

| Format | Example | Meaning |
|---|---|---|
| TC-S{N}-API-{###} | TC-S3-API-012 | Sprint 3, API layer, case #12 |
| TC-S{N}-WEB-{###} | TC-S1-WEB-006 | Sprint 1, Web UI layer, case #6 |
| TC-S{N}-MOB-{###} | TC-S2-MOB-003 | Sprint 2, Mobile layer, case #3 |

---

## 2. Master Coverage Summary — All Sprints

| Sprint | Feature | API | Web | Mobile | Total | Status |
|---|---|---|---|---|---|---|
| 0 | Infrastructure & Setup | 15 | — | — | 15 | **Done** |
| 1 | Auth & User Management | 40 | 25 | 20 | 85 | **Done** |
| 2 | Buildings & Apartments | 35 | 20 | 15 | 70 | **Planned** |
| 3 | Expense Management | 40 | 22 | 18 | 80 | **Planned** |
| 4 | Payment Management | 35 | 20 | 15 | 70 | **Planned** |
| 5 | Dashboards (Web Only) | 15 | 22 | — | 37 | **Planned** |
| 6 | Notifications | 20 | 15 | 15 | 50 | **Planned** |
| 7 | Flutter Finalization | 10 | — | 28 | 38 | **Planned** |
| 8 | Audit & Data Exports | 18 | 14 | 8 | 40 | **Planned** |
| 9 | Performance & Security | 20 | 10 | 5 | 35 | **Planned** |
| 10 | Regression & Deployment | — | — | — | Full Suite | **Planned** |
| **TOTAL** | | | | | **480+** | |

---

## 3. Sprint Test Cases — Full Detail

### Sprint 0 — Infrastructure & Architecture Setup

These 15 API tests validate the project scaffolding before any feature development begins. Every test must pass at 100% before Sprint 1 work is merged into the main branch.

*Run command: pytest -m sprint0 -v*

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S0-001 | Health endpoint GET /api/health/ returns HTTP 200 | API | Health Check | Positive |
| TC-S0-002 | Health response body contains { "status": "ok" } | API | Health Check | Positive |
| TC-S0-003 | Health endpoint responds in under 500ms (NFR baseline) | API | Performance | Performance |
| TC-S0-004 | Unknown endpoint returns 404, not 500 (no unhandled exceptions) | API | Error Handling | Negative |
| TC-S0-005 | API base URL contains /v1/ versioning prefix | API | Architecture | Positive |
| TC-S0-006 | All responses return Content-Type: application/json header | API | Security Headers | Security |
| TC-S0-007 | X-Frame-Options header is DENY or SAMEORIGIN on all responses | API | Security Headers | Security |
| TC-S0-008 | X-Content-Type-Options: nosniff present on all responses | API | Security Headers | Security |
| TC-S0-009 | Server header does NOT disclose software name or version | API | Security Headers | Security |
| TC-S0-010 | Referrer-Policy header is set (not empty) | API | Security Headers | Security |
| TC-S0-011 | CORS OPTIONS rejects requests from unknown/evil origins | API | CORS | Security |
| TC-S0-012 | CORS allows preflight from the legitimate frontend origin | API | CORS | Positive |
| TC-S0-013 | OPTIONS preflight to /auth/login/ returns 200 or 204 | API | CORS | Positive |
| TC-S0-014 | POST /auth/login/ with wrong creds returns 400/401, not 500 (DB probe) | API | DB Connectivity | Positive |
| TC-S0-015 | Every API response is valid JSON — no HTML error pages returned | API | Response Format | Positive |

---

### Sprint 1 — Authentication & User Management (85 Cases)

The most security-critical sprint. RBAC failures can expose all tenant data. Every auth edge case, injection vector, and role boundary is tested.

*Run command: pytest -m sprint1 -v*

#### Sprint 1 — API Tests (40 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S1-API-001 | Admin login with valid credentials returns HTTP 200 + access + refresh tokens | API | Login | Positive |
| TC-S1-API-002 | Owner login with valid credentials returns HTTP 200 + both tokens | API | Login | Positive |
| TC-S1-API-003 | Access token is a valid JWT with user_id, role, and exp claims | API | Token | Positive |
| TC-S1-API-004 | JWT issued to Admin contains role=Admin claim | API | Token | Positive |
| TC-S1-API-005 | JWT issued to Owner contains role=Owner claim | API | Token | Positive |
| TC-S1-API-006 | Login response time is under 500ms (NFR) | API | Performance | Performance |
| TC-S1-API-007 | Login with email in UPPERCASE is accepted (case-insensitive) | API | Login | Positive |
| TC-S1-API-008 | Wrong password returns HTTP 401 | API | Login | Negative |
| TC-S1-API-009 | Non-existent email returns HTTP 401 (not 404) | API | Login | Negative |
| TC-S1-API-010 | Error message does not confirm whether email exists (anti-enumeration) | API | Security | Security |
| TC-S1-API-011 | Empty email field returns HTTP 400 | API | Validation | Negative |
| TC-S1-API-012 | Empty password field returns HTTP 400 | API | Validation | Negative |
| TC-S1-API-013 | Missing email field in body returns HTTP 400 | API | Validation | Negative |
| TC-S1-API-014 | Missing password field in body returns HTTP 400 | API | Validation | Negative |
| TC-S1-API-015 | Empty JSON body {} returns HTTP 400 | API | Validation | Negative |
| TC-S1-API-016 | Malformed email format (not@valid) returns HTTP 400 | API | Validation | Negative |
| TC-S1-API-017 | SQL injection in email field returns 400/401, never 200 or 500 | API | Security | Security |
| TC-S1-API-018 | XSS payload in email field is not reflected unescaped in response | API | Security | Security |
| TC-S1-API-019 | 7 weak password variants are all rejected with 400 on registration | API | Security | Security |
| TC-S1-API-020 | Valid refresh token generates a new access token (200) | API | Token | Positive |
| TC-S1-API-021 | Forged/invalid refresh token returns HTTP 401 | API | Token | Negative |
| TC-S1-API-022 | Missing refresh token in body returns HTTP 400 | API | Token | Negative |
| TC-S1-API-023 | Logout blacklists the refresh token — reuse after logout returns 401 | API | Security | Security |
| TC-S1-API-024 | Expired or forged access token on any endpoint returns 401 | API | Security | Security |
| TC-S1-API-025 | Unauthenticated request to /buildings/ returns 401 | API | RBAC | Security |
| TC-S1-API-026 | Owner POST /buildings/ is forbidden — returns 403 | API | RBAC | Security |
| TC-S1-API-027 | Owner GET /users/ is forbidden — returns 403 | API | RBAC | Security |
| TC-S1-API-028 | Owner POST /users/ is forbidden — returns 403 | API | RBAC | Security |
| TC-S1-API-029 | Admin GET /buildings/ returns 200 with all buildings | API | RBAC | Positive |
| TC-S1-API-030 | Admin GET /users/ returns 200 with all users | API | RBAC | Positive |
| TC-S1-API-031 | Owner cannot access a building they are not assigned to (403 or 404) | API | Multi-Tenant | Security |
| TC-S1-API-032 | Admin creates new user — returns 201 with id and email | API | User CRUD | Positive |
| TC-S1-API-033 | Password and password_hash never appear in any user API response | API | Security | Security |
| TC-S1-API-034 | Duplicate email registration returns HTTP 400 | API | Validation | Negative |
| TC-S1-API-035 | Admin deactivates user — is_active becomes false | API | User CRUD | Positive |
| TC-S1-API-036 | Deactivated user cannot log in — returns 401 | API | User CRUD | Negative |
| TC-S1-API-037 | Password change with correct current password returns 200/204 | API | User CRUD | Positive |
| TC-S1-API-038 | Password change with wrong current password returns 400 | API | User CRUD | Negative |
| TC-S1-API-039 | Password confirm mismatch returns 400 | API | User CRUD | Negative |
| TC-S1-API-040 | Account locks after 5 consecutive failed logins (returns 401/423) | API | Security | Security |

#### Sprint 1 — Web UI Tests (25 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S1-WEB-001 | Login page title contains ABEM or Login | Web | Rendering | Positive |
| TC-S1-WEB-002 | Email input field is visible on login page | Web | Rendering | Positive |
| TC-S1-WEB-003 | Password input field is visible on login page | Web | Rendering | Positive |
| TC-S1-WEB-004 | Password field is type=password (masked) by default | Web | Security | Security |
| TC-S1-WEB-005 | Login submit button is visible and enabled | Web | Rendering | Positive |
| TC-S1-WEB-006 | Admin login redirects to /dashboard | Web | Auth Flow | Positive |
| TC-S1-WEB-007 | Owner login redirects to /dashboard | Web | Auth Flow | Positive |
| TC-S1-WEB-008 | Admin dashboard shows admin-only controls (buildings, users) | Web | RBAC | Positive |
| TC-S1-WEB-009 | Owner dashboard does NOT show admin-only controls | Web | RBAC | Security |
| TC-S1-WEB-010 | Browser Back after logout does not expose dashboard | Web | Security | Security |
| TC-S1-WEB-011 | Wrong password shows inline error — no dashboard redirect | Web | Error UX | Negative |
| TC-S1-WEB-012 | Error message is generic — does not confirm email existence | Web | Security | Security |
| TC-S1-WEB-013 | Empty form submission shows validation errors | Web | Validation | Negative |
| TC-S1-WEB-014 | Empty email prevents form submission | Web | Validation | Negative |
| TC-S1-WEB-015 | Empty password prevents form submission | Web | Validation | Negative |
| TC-S1-WEB-016 | Show/hide password toggle changes field type password ↔ text | Web | Security UX | Positive |
| TC-S1-WEB-017 | /login is accessible to unauthenticated users (no redirect loop) | Web | Routing | Positive |
| TC-S1-WEB-018 | Direct navigation to /dashboard redirects unauth user to /login | Web | Security | Security |
| TC-S1-WEB-019 | Login page is served over HTTPS in staging/prod environments | Web | Security | Security |
| TC-S1-WEB-020 | Forgot Password link navigates to /forgot-password | Web | Navigation | Positive |
| TC-S1-WEB-021 | Tab key navigates email → password → submit in order | Web | Accessibility | Positive |
| TC-S1-WEB-022 | Enter key in password field submits the login form | Web | Accessibility | Positive |
| TC-S1-WEB-023 | Email input has type=email (browser validation + mobile keyboard) | Web | Accessibility | Positive |
| TC-S1-WEB-024 | Password field has autocomplete=current-password | Web | Accessibility | Positive |
| TC-S1-WEB-025 | No horizontal scroll at 375px viewport (mobile responsive) | Web | Responsive | Positive |

#### Sprint 1 — Mobile Tests (20 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S1-MOB-001 | Login screen is shown on first app launch | Mobile | Rendering | Mobile |
| TC-S1-MOB-002 | Email input is visible and enabled on login screen | Mobile | Rendering | Mobile |
| TC-S1-MOB-003 | Password input is visible and text is obscured | Mobile | Security | Security |
| TC-S1-MOB-004 | Login button is visible and tappable | Mobile | Rendering | Mobile |
| TC-S1-MOB-005 | Tapping email field raises the soft keyboard | Mobile | UX | Mobile |
| TC-S1-MOB-006 | Admin login navigates to Buildings screen (no dashboard on mobile) | Mobile | Auth Flow | Mobile |
| TC-S1-MOB-007 | Owner login navigates to Owner Home / Balance screen | Mobile | Auth Flow | Mobile |
| TC-S1-MOB-008 | Token persists after backgrounding — user stays logged in | Mobile | Security | Security |
| TC-S1-MOB-009 | Admin sees Buildings, Expenses, Payments in navigation | Mobile | RBAC | Mobile |
| TC-S1-MOB-010 | Owner does NOT see user management or all-buildings nav items | Mobile | RBAC | Security |
| TC-S1-MOB-011 | Wrong password shows error message — stays on login screen | Mobile | Error UX | Negative |
| TC-S1-MOB-012 | Empty fields tap login shows validation — no API call | Mobile | Validation | Negative |
| TC-S1-MOB-013 | Loading indicator shown during login request | Mobile | UX | Mobile |
| TC-S1-MOB-014 | Login button disabled during in-flight request (no double-submit) | Mobile | UX | Mobile |
| TC-S1-MOB-015 | Logout clears secure storage — reopening shows login screen | Mobile | Security | Security |
| TC-S1-MOB-016 | User can view their profile (name, email) from profile screen | Mobile | Profile | Mobile |
| TC-S1-MOB-017 | User can update phone number from profile screen | Mobile | Profile | Mobile |
| TC-S1-MOB-018 | Invalid phone format shows validation error | Mobile | Profile | Negative |
| TC-S1-MOB-019 | Password change requires correct current password on mobile | Mobile | Profile | Negative |
| TC-S1-MOB-020 | Session expires gracefully — app redirects to login with message | Mobile | Security | Security |

---

### Sprint 2 — Buildings & Apartment Management (70 Cases)

Tests the core data model of the platform. Tenant isolation (multi-building) is the highest-risk area — an owner viewing another building's data is a critical defect.

*Run command: pytest -m sprint2 -v*

#### Sprint 2 — API Tests (35 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S2-API-001 | Admin POST /buildings/ with valid data returns 201 + building object | API | Building CRUD | Positive |
| TC-S2-API-002 | Created building response contains id, name, address, num_floors, tenant_id | API | Building CRUD | Positive |
| TC-S2-API-003 | Admin GET /buildings/ returns list of all buildings (200) | API | Building CRUD | Positive |
| TC-S2-API-004 | Admin GET /buildings/{id}/ returns single building detail (200) | API | Building CRUD | Positive |
| TC-S2-API-005 | Admin PATCH /buildings/{id}/ updates name and returns updated object | API | Building CRUD | Positive |
| TC-S2-API-006 | Admin DELETE /buildings/{id}/ soft-deletes — returns 200/204 | API | Building CRUD | Positive |
| TC-S2-API-007 | Soft-deleted building returns 404 on subsequent GET | API | Building CRUD | Positive |
| TC-S2-API-008 | POST /buildings/ with missing name returns 400 | API | Validation | Negative |
| TC-S2-API-009 | POST /buildings/ with missing address returns 400 | API | Validation | Negative |
| TC-S2-API-010 | POST /buildings/ with num_floors=0 returns 400 | API | Validation | Negative |
| TC-S2-API-011 | POST /buildings/ with negative num_apartments returns 400 | API | Validation | Negative |
| TC-S2-API-012 | Owner cannot GET /buildings/ of buildings not assigned to them | API | Multi-Tenant | Security |
| TC-S2-API-013 | Owner A cannot see Owner B building data (tenant isolation) | API | Multi-Tenant | Security |
| TC-S2-API-014 | Building response does NOT include other tenant data | API | Multi-Tenant | Security |
| TC-S2-API-015 | Admin can assign owner to a building (POST /buildings/{id}/assign-user/) | API | Assignment | Positive |
| TC-S2-API-016 | Assigned owner can now GET /buildings/{id}/ (200) | API | Assignment | Positive |
| TC-S2-API-017 | Admin POST /apartments/ with valid data returns 201 | API | Apartment CRUD | Positive |
| TC-S2-API-018 | Apartment response contains id, floor, size, type, building_id | API | Apartment CRUD | Positive |
| TC-S2-API-019 | Admin GET /buildings/{id}/apartments/ lists all apartments | API | Apartment CRUD | Positive |
| TC-S2-API-020 | Admin PATCH /apartments/{id}/ updates floor and size | API | Apartment CRUD | Positive |
| TC-S2-API-021 | Admin DELETE /apartments/{id}/ soft-deletes apartment | API | Apartment CRUD | Positive |
| TC-S2-API-022 | POST /apartments/ with invalid type (not Apartment/Store) returns 400 | API | Validation | Negative |
| TC-S2-API-023 | POST /apartments/ with floor > building num_floors returns 400 | API | Validation | Negative |
| TC-S2-API-024 | Owner can GET their own apartment details | API | Apartment | Positive |
| TC-S2-API-025 | Owner cannot GET another apartment in the same building (403/404) | API | Multi-Tenant | Security |
| TC-S2-API-026 | Admin assigns owner to apartment (PATCH owner_id) | API | Assignment | Positive |
| TC-S2-API-027 | Apartment type Store is correctly stored and returned | API | Apartment CRUD | Positive |
| TC-S2-API-028 | Search /buildings/?search=name returns filtered results | API | Search | Positive |
| TC-S2-API-029 | Filter /apartments/?type=Store returns only stores | API | Filter | Positive |
| TC-S2-API-030 | Filter /apartments/?building_id={id} scopes results correctly | API | Filter | Positive |
| TC-S2-API-031 | List endpoints return paginated results (next/previous links) | API | Pagination | Positive |
| TC-S2-API-032 | GET /buildings/?page=999 returns empty results, not error | API | Pagination | Negative |
| TC-S2-API-033 | Admin can manage multiple buildings — all appear in GET /buildings/ | API | Multi-Building | Positive |
| TC-S2-API-034 | tenant_id is auto-generated UUID on building creation (not user-supplied) | API | Security | Security |
| TC-S2-API-035 | Apartment balance field initializes to 0.00 on creation | API | Data Integrity | Positive |

#### Sprint 2 — Web UI Tests (20 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S2-WEB-001 | Buildings list page loads and shows table of all buildings | Web | Building UI | Positive |
| TC-S2-WEB-002 | Add Building form has all required fields (name, address, floors, units) | Web | Building UI | Positive |
| TC-S2-WEB-003 | Admin submits valid building form — new building appears in list | Web | Building UI | Positive |
| TC-S2-WEB-004 | Form validation shows error if name is blank on submit | Web | Validation | Negative |
| TC-S2-WEB-005 | Form validation shows error if num_floors is not a positive integer | Web | Validation | Negative |
| TC-S2-WEB-006 | Edit building — changes saved and reflected in list | Web | Building UI | Positive |
| TC-S2-WEB-007 | Delete building shows confirmation dialog before deleting | Web | Building UI | Positive |
| TC-S2-WEB-008 | Deleted building disappears from list after confirmation | Web | Building UI | Positive |
| TC-S2-WEB-009 | Apartments list loads within selected building context | Web | Apartment UI | Positive |
| TC-S2-WEB-010 | Add Apartment form has floor, size, type (Apartment/Store), owner fields | Web | Apartment UI | Positive |
| TC-S2-WEB-011 | Admin assigns owner to apartment from dropdown — saved correctly | Web | Assignment | Positive |
| TC-S2-WEB-012 | Owner dashboard shows only their assigned building — no others | Web | RBAC | Security |
| TC-S2-WEB-013 | Building selector dropdown works for admin with multiple buildings | Web | Multi-Building | Positive |
| TC-S2-WEB-014 | Switching building in selector updates all data on page | Web | Multi-Building | Positive |
| TC-S2-WEB-015 | Search box filters building list by name in real-time | Web | Search | Positive |
| TC-S2-WEB-016 | Apartment type badge shows Apartment or Store label correctly | Web | Apartment UI | Positive |
| TC-S2-WEB-017 | Apartment floor number displayed correctly in list | Web | Apartment UI | Positive |
| TC-S2-WEB-018 | Building card shows count of apartments and stores | Web | Building UI | Positive |
| TC-S2-WEB-019 | Owner view of apartment details is read-only (no edit buttons) | Web | RBAC | Security |
| TC-S2-WEB-020 | Responsive: Building list is usable on 768px tablet viewport | Web | Responsive | Positive |

#### Sprint 2 — Mobile Tests (15 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S2-MOB-001 | Buildings list screen shows after admin login | Mobile | Building UI | Mobile |
| TC-S2-MOB-002 | Admin can create a new building from mobile | Mobile | Building UI | Mobile |
| TC-S2-MOB-003 | New building appears in list immediately after creation | Mobile | Building UI | Mobile |
| TC-S2-MOB-004 | Admin can edit building name from mobile | Mobile | Building UI | Mobile |
| TC-S2-MOB-005 | Admin can view apartment list within a building | Mobile | Apartment UI | Mobile |
| TC-S2-MOB-006 | Owner sees only their assigned building in the list | Mobile | RBAC | Security |
| TC-S2-MOB-007 | Owner taps building — sees apartment details screen | Mobile | Apartment UI | Mobile |
| TC-S2-MOB-008 | Building switcher allows admin to switch between buildings | Mobile | Multi-Building | Mobile |
| TC-S2-MOB-009 | Apartment type (Apartment/Store) shown with icon/badge | Mobile | Apartment UI | Mobile |
| TC-S2-MOB-010 | Search bar filters buildings list on mobile | Mobile | Search | Mobile |
| TC-S2-MOB-011 | Pull-to-refresh reloads building list from API | Mobile | UX | Mobile |
| TC-S2-MOB-012 | Tapping apartment shows floor, size, owner name, balance | Mobile | Apartment UI | Mobile |
| TC-S2-MOB-013 | Admin can assign owner to apartment from mobile | Mobile | Assignment | Mobile |
| TC-S2-MOB-014 | Empty building list shows helpful empty state message | Mobile | UX | Mobile |
| TC-S2-MOB-015 | Building data loads within 3 seconds on mobile connection | Mobile | Performance | Performance |

---

### Sprint 3 — Expense Management (80 Cases)

The expense split engine and rounding logic are the core financial calculations of the system. Incorrect rounding or wrong split distribution directly affects what owners owe. These tests are P0.

*Run command: pytest -m sprint3 -v*

#### Sprint 3 — API Tests (40 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S3-API-001 | Admin POST /expenses/ with valid data returns 201 + expense object | API | Expense CRUD | Positive |
| TC-S3-API-002 | Expense response contains id, amount, category_id, date_incurred, building_id | API | Expense CRUD | Positive |
| TC-S3-API-003 | GET /expenses/?building_id={id} returns all expenses for that building | API | Expense CRUD | Positive |
| TC-S3-API-004 | GET /expenses/{id}/ returns expense detail with apartment shares | API | Expense CRUD | Positive |
| TC-S3-API-005 | PATCH /expenses/{id}/ updates amount — creates audit log entry | API | Expense CRUD | Positive |
| TC-S3-API-006 | DELETE /expenses/{id}/ soft-deletes — subsequent GET returns 404 | API | Expense CRUD | Positive |
| TC-S3-API-007 | POST /expenses/ with amount=0 returns 400 | API | Validation | Negative |
| TC-S3-API-008 | POST /expenses/ with negative amount returns 400 | API | Validation | Negative |
| TC-S3-API-009 | POST /expenses/ with missing category_id returns 400 | API | Validation | Negative |
| TC-S3-API-010 | POST /expenses/ with missing date_incurred returns 400 | API | Validation | Negative |
| TC-S3-API-011 | POST /expenses/ with future date is accepted (valid business case) | API | Validation | Positive |
| TC-S3-API-012 | Equal split: 100.00 / 4 apartments = 25.00 each (exact) | API | Split Engine | Positive |
| TC-S3-API-013 | Equal split: 101.00 / 4 apartments rounds UP to 30.00 each (nearest 5) | API | Split Engine | Positive |
| TC-S3-API-014 | Equal split: 103.00 / 3 apartments rounds UP to 35.00 each | API | Split Engine | Positive |
| TC-S3-API-015 | Type-based split: expense applies to apartments only — stores excluded | API | Split Engine | Positive |
| TC-S3-API-016 | Type-based split: expense applies to stores only — apartments excluded | API | Split Engine | Positive |
| TC-S3-API-017 | Custom subset split: only selected apartments receive a share | API | Split Engine | Positive |
| TC-S3-API-018 | Rounding is always UP — never down or to nearest | API | Split Engine | Positive |
| TC-S3-API-019 | Split on a building with 1 apartment assigns full expense to that unit | API | Split Engine | Positive |
| TC-S3-API-020 | Total collected after rounding is >= original expense amount | API | Split Engine | Positive |
| TC-S3-API-021 | Creating expense triggers apartment_expenses rows for all affected units | API | Split Engine | Positive |
| TC-S3-API-022 | Each apartment_expenses row has correct share_amount after split | API | Data Integrity | Positive |
| TC-S3-API-023 | POST /expenses/ with is_recurring=true creates a recurring_config row | API | Recurring | Positive |
| TC-S3-API-024 | Recurring config with frequency=monthly stores next_due_date correctly | API | Recurring | Positive |
| TC-S3-API-025 | Recurring config with frequency=quarterly stores correct next_due | API | Recurring | Positive |
| TC-S3-API-026 | Scheduled job generates new expense from recurring config on due date | API | Recurring | Positive |
| TC-S3-API-027 | Generated recurring expense inherits category and split type from config | API | Recurring | Positive |
| TC-S3-API-028 | POST /expenses/{id}/upload/ with JPEG returns 200 and media record | API | File Upload | Positive |
| TC-S3-API-029 | POST /expenses/{id}/upload/ with PNG returns 200 | API | File Upload | Positive |
| TC-S3-API-030 | POST /expenses/{id}/upload/ with PDF returns 200 | API | File Upload | Positive |
| TC-S3-API-031 | POST /expenses/{id}/upload/ with EXE file returns 400 (type rejected) | API | File Upload | Security |
| TC-S3-API-032 | POST /expenses/{id}/upload/ with file > 10MB returns 413 | API | File Upload | Negative |
| TC-S3-API-033 | Uploaded file URL in response is pre-signed (has expiry token) | API | File Upload | Security |
| TC-S3-API-034 | Owner can GET expenses for their building (200) | API | RBAC | Positive |
| TC-S3-API-035 | Owner cannot POST new expenses (403) | API | RBAC | Security |
| TC-S3-API-036 | Owner cannot PATCH existing expense (403) | API | RBAC | Security |
| TC-S3-API-037 | Expense categories are building-scoped — GET /categories/?building_id= | API | Categories | Positive |
| TC-S3-API-038 | Admin can create custom expense category for a building | API | Categories | Positive |
| TC-S3-API-039 | Filter /expenses/?date_from=&date_to= returns correct date range | API | Filter | Positive |
| TC-S3-API-040 | Filter /expenses/?category_id={id} returns only matching expenses | API | Filter | Positive |

#### Sprint 3 — Web UI Tests (22 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S3-WEB-001 | Expenses list page shows table with amount, category, date, status | Web | Expense UI | Positive |
| TC-S3-WEB-002 | Add Expense form has fields for amount, category, description, date | Web | Expense UI | Positive |
| TC-S3-WEB-003 | Split type selector shows options: Equal, Apartments Only, Stores Only | Web | Expense UI | Positive |
| TC-S3-WEB-004 | Submitting valid expense shows new record in list | Web | Expense UI | Positive |
| TC-S3-WEB-005 | Amount field only accepts positive numbers | Web | Validation | Negative |
| TC-S3-WEB-006 | Date picker defaults to today | Web | Expense UI | Positive |
| TC-S3-WEB-007 | After split, per-unit share amounts shown in expense detail | Web | Split Display | Positive |
| TC-S3-WEB-008 | Rounded amounts shown — not raw decimal values | Web | Split Display | Positive |
| TC-S3-WEB-009 | Edit expense changes amount and triggers re-split on save | Web | Expense UI | Positive |
| TC-S3-WEB-010 | Delete expense shows confirmation and removes from list | Web | Expense UI | Positive |
| TC-S3-WEB-011 | Recurring checkbox reveals frequency selector (Monthly/Quarterly/Annual) | Web | Recurring UI | Positive |
| TC-S3-WEB-012 | Recurring expense shows recurring badge in list | Web | Recurring UI | Positive |
| TC-S3-WEB-013 | Bill image upload button opens file picker | Web | File Upload | Positive |
| TC-S3-WEB-014 | Uploaded bill image thumbnail shown in expense detail | Web | File Upload | Positive |
| TC-S3-WEB-015 | File type error message shown for unsupported format | Web | File Upload | Negative |
| TC-S3-WEB-016 | Date range filter narrows expense list correctly | Web | Filter | Positive |
| TC-S3-WEB-017 | Category filter shows only expenses of selected category | Web | Filter | Positive |
| TC-S3-WEB-018 | Owner can view expense list but has no Add/Edit/Delete buttons | Web | RBAC | Security |
| TC-S3-WEB-019 | Expense total and per-unit breakdown shown in detail panel | Web | Expense UI | Positive |
| TC-S3-WEB-020 | Building selector filters expenses to selected building | Web | Multi-Building | Positive |
| TC-S3-WEB-021 | Expense list shows status badge: Paid / Unpaid / Partial | Web | Expense UI | Positive |
| TC-S3-WEB-022 | Long description text is truncated in list, full text in detail | Web | Expense UI | Positive |

#### Sprint 3 — Mobile Tests (18 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S3-MOB-001 | Expenses screen shows list for current building | Mobile | Expense UI | Mobile |
| TC-S3-MOB-002 | Admin can create expense from mobile with amount and category | Mobile | Expense UI | Mobile |
| TC-S3-MOB-003 | Camera button opens device camera for bill image capture | Mobile | File Upload | Mobile |
| TC-S3-MOB-004 | Gallery button opens device photo gallery | Mobile | File Upload | Mobile |
| TC-S3-MOB-005 | Captured bill image uploads and links to expense | Mobile | File Upload | Mobile |
| TC-S3-MOB-006 | Image upload progress indicator shown during upload | Mobile | File Upload | Mobile |
| TC-S3-MOB-007 | Upload fails gracefully if file too large — shows error toast | Mobile | File Upload | Negative |
| TC-S3-MOB-008 | Owner can view expense list (read-only) | Mobile | RBAC | Mobile |
| TC-S3-MOB-009 | Owner does not see Add Expense button | Mobile | RBAC | Security |
| TC-S3-MOB-010 | Expense detail screen shows per-unit share and building info | Mobile | Expense UI | Mobile |
| TC-S3-MOB-011 | Recurring indicator shown on recurring expenses in list | Mobile | Recurring UI | Mobile |
| TC-S3-MOB-012 | Pull-to-refresh updates expense list from API | Mobile | UX | Mobile |
| TC-S3-MOB-013 | Filter by category narrows mobile expense list | Mobile | Filter | Mobile |
| TC-S3-MOB-014 | Bill image thumbnail tappable — opens full-screen viewer | Mobile | File Upload | Mobile |
| TC-S3-MOB-015 | Expense amount displayed with currency formatting (e.g. 1,500.00) | Mobile | Expense UI | Mobile |
| TC-S3-MOB-016 | Creating expense with no network shows offline error message | Mobile | Offline | Negative |
| TC-S3-MOB-017 | Admin can delete expense from mobile — confirms with dialog | Mobile | Expense UI | Mobile |
| TC-S3-MOB-018 | Expense list loads within 3s on mobile (performance) | Mobile | Performance | Performance |

---

### Sprint 4 — Payment Management (70 Cases)

Payment recording involves real money and carry-forward balance logic. Overpayment handling and balance recalculation must be mathematically precise. All financial assertions use exact decimal comparisons.

*Run command: pytest -m sprint4 -v*

#### Sprint 4 — API Tests (35 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S4-API-001 | Admin POST /payments/ with valid data returns 201 + payment object | API | Payment CRUD | Positive |
| TC-S4-API-002 | Payment response contains apartment_id, expense_id, amount_paid, date_paid, method | API | Payment CRUD | Positive |
| TC-S4-API-003 | GET /payments/?apartment_id={id} returns all payments for that unit | API | Payment CRUD | Positive |
| TC-S4-API-004 | GET /apartments/{id}/balance/ returns current outstanding balance | API | Balance | Positive |
| TC-S4-API-005 | Exact payment: balance becomes 0.00 after exact amount paid | API | Balance | Positive |
| TC-S4-API-006 | Partial payment: balance reduced by amount_paid, not zeroed | API | Balance | Positive |
| TC-S4-API-007 | Overpayment: balance goes negative (credit) after paying more than owed | API | Overpayment | Positive |
| TC-S4-API-008 | Credit balance auto-deducted from next expense assignment | API | Overpayment | Positive |
| TC-S4-API-009 | Carry-forward: credit of 50.00 reduces next bill of 200.00 to 150.00 | API | Overpayment | Positive |
| TC-S4-API-010 | Multiple partial payments accumulate correctly to zero balance | API | Balance | Positive |
| TC-S4-API-011 | Payment history shows all transactions in chronological order | API | History | Positive |
| TC-S4-API-012 | Each payment record snapshots remaining_balance at time of payment | API | History | Positive |
| TC-S4-API-013 | POST /payments/ with amount=0 returns 400 | API | Validation | Negative |
| TC-S4-API-014 | POST /payments/ with negative amount returns 400 | API | Validation | Negative |
| TC-S4-API-015 | POST /payments/ with non-existent apartment_id returns 404 | API | Validation | Negative |
| TC-S4-API-016 | POST /payments/ with non-existent expense_id returns 404 | API | Validation | Negative |
| TC-S4-API-017 | POST /payments/ with missing amount_paid returns 400 | API | Validation | Negative |
| TC-S4-API-018 | POST /payments/ with missing date_paid returns 400 | API | Validation | Negative |
| TC-S4-API-019 | payment_method field accepts: cash, bank_transfer, cheque | API | Validation | Positive |
| TC-S4-API-020 | payment_method field rejects unknown values — returns 400 | API | Validation | Negative |
| TC-S4-API-021 | Owner can GET their own payment history (200) | API | RBAC | Positive |
| TC-S4-API-022 | Owner cannot GET another apartment payment history (403/404) | API | RBAC | Security |
| TC-S4-API-023 | Owner cannot POST a payment (admin-only action) — returns 403 | API | RBAC | Security |
| TC-S4-API-024 | Balance is recalculated immediately after payment recorded | API | Balance | Positive |
| TC-S4-API-025 | Balance uses DECIMAL precision — no floating point rounding errors | API | Data Integrity | Positive |
| TC-S4-API-026 | Payment with amount exceeding balance still succeeds (overpayment allowed) | API | Overpayment | Positive |
| TC-S4-API-027 | Deleting an expense recalculates affected apartment balances | API | Data Integrity | Positive |
| TC-S4-API-028 | GET /apartments/{id}/balance/ returns breakdown: owed, paid, credit | API | Balance | Positive |
| TC-S4-API-029 | Filter /payments/?date_from=&date_to= returns correct range | API | Filter | Positive |
| TC-S4-API-030 | Filter /payments/?method=cash returns only cash payments | API | Filter | Positive |
| TC-S4-API-031 | Multiple concurrent payments do not cause race condition on balance | API | Data Integrity | Positive |
| TC-S4-API-032 | Payment for expense not assigned to apartment returns 400 | API | Validation | Negative |
| TC-S4-API-033 | Admin can view ALL payment history across all buildings | API | RBAC | Positive |
| TC-S4-API-034 | Payment records are immutable — no PATCH or DELETE allowed | API | Data Integrity | Security |
| TC-S4-API-035 | Overpaid credit does not apply to other tenants (isolation) | API | Multi-Tenant | Security |

#### Sprint 4 — Web UI Tests (20 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S4-WEB-001 | Record Payment form has fields: amount, date, method, apartment, expense | Web | Payment UI | Positive |
| TC-S4-WEB-002 | Admin submits valid payment — confirmation message shown | Web | Payment UI | Positive |
| TC-S4-WEB-003 | Balance displayed on apartment detail page updates after payment | Web | Balance UI | Positive |
| TC-S4-WEB-004 | Balance shows colour coding: green=paid, amber=partial, red=overdue | Web | Balance UI | Positive |
| TC-S4-WEB-005 | Overpayment shows negative balance with credit label | Web | Balance UI | Positive |
| TC-S4-WEB-006 | Payment history table shows date, amount, method, balance snapshot | Web | History UI | Positive |
| TC-S4-WEB-007 | Amount field only accepts positive numbers | Web | Validation | Negative |
| TC-S4-WEB-008 | Date picker defaults to today for payment date | Web | Payment UI | Positive |
| TC-S4-WEB-009 | Payment method dropdown has all options (cash, bank transfer, cheque) | Web | Payment UI | Positive |
| TC-S4-WEB-010 | Partial payment: balance shown reduced correctly on screen | Web | Balance UI | Positive |
| TC-S4-WEB-011 | Carry-forward credit shown in payment breakdown panel | Web | Overpayment UI | Positive |
| TC-S4-WEB-012 | Owner can view own payment history (read-only list) | Web | RBAC | Positive |
| TC-S4-WEB-013 | Owner has no Record Payment button | Web | RBAC | Security |
| TC-S4-WEB-014 | Overdue label appears on apartments with past-due balance | Web | Balance UI | Positive |
| TC-S4-WEB-015 | Payment totals in building overview match sum of individual payments | Web | Data Integrity | Positive |
| TC-S4-WEB-016 | Print/export payment receipt button visible after recording payment | Web | Payment UI | Positive |
| TC-S4-WEB-017 | Payment history can be filtered by date range | Web | Filter | Positive |
| TC-S4-WEB-018 | Apartments with zero balance shown differently from those with balance | Web | Balance UI | Positive |
| TC-S4-WEB-019 | Admin can view all overdue apartments across all buildings | Web | Admin UI | Positive |
| TC-S4-WEB-020 | Responsive: payment form usable on 375px mobile viewport | Web | Responsive | Positive |

#### Sprint 4 — Mobile Tests (15 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S4-MOB-001 | Owner home screen shows current outstanding balance prominently | Mobile | Balance UI | Mobile |
| TC-S4-MOB-002 | Balance updates in real-time after admin records payment | Mobile | Balance UI | Mobile |
| TC-S4-MOB-003 | Payment history list shows transactions in reverse chronological order | Mobile | History UI | Mobile |
| TC-S4-MOB-004 | Admin can record payment from mobile — form with amount, method, date | Mobile | Payment UI | Mobile |
| TC-S4-MOB-005 | Admin selects apartment from searchable list when recording payment | Mobile | Payment UI | Mobile |
| TC-S4-MOB-006 | Payment confirmation dialog shown before submitting | Mobile | UX | Mobile |
| TC-S4-MOB-007 | After recording payment, balance on screen updates immediately | Mobile | Balance UI | Mobile |
| TC-S4-MOB-008 | Overpayment credit shown in green with credit label | Mobile | Balance UI | Mobile |
| TC-S4-MOB-009 | Owner cannot see Record Payment button or form | Mobile | RBAC | Security |
| TC-S4-MOB-010 | Pull-to-refresh on payment history fetches latest data | Mobile | UX | Mobile |
| TC-S4-MOB-011 | Payment with no network shows offline error toast | Mobile | Offline | Negative |
| TC-S4-MOB-012 | Large balance numbers formatted with thousands separator | Mobile | UX | Mobile |
| TC-S4-MOB-013 | Payment method icon/label shown in history list items | Mobile | History UI | Mobile |
| TC-S4-MOB-014 | Balance breakdown: total owed, total paid, credit shown in detail | Mobile | Balance UI | Mobile |
| TC-S4-MOB-015 | Payment list loads within 3 seconds on mobile | Mobile | Performance | Performance |

---

### Sprint 5 — Dashboards / Web Only (37 Cases)

Dashboard is a Web-only feature. No Mobile tests for this sprint. Tests focus on data accuracy of aggregations, chart rendering, and date filter correctness.

*Run command: pytest -m sprint5 -v*

#### Sprint 5 — API Tests (15 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S5-API-001 | GET /dashboard/admin/ returns 200 with building summary data | API | Admin Dashboard | Positive |
| TC-S5-API-002 | Admin dashboard totals: total_income, total_expenses, overdue_count | API | Admin Dashboard | Positive |
| TC-S5-API-003 | overdue_count matches apartments with balance > 0 past due date | API | Admin Dashboard | Positive |
| TC-S5-API-004 | GET /dashboard/owner/ returns 200 with owner-specific data | API | Owner Dashboard | Positive |
| TC-S5-API-005 | Owner dashboard contains balance_summary, recent_payments, expense_breakdown | API | Owner Dashboard | Positive |
| TC-S5-API-006 | expense_breakdown grouped by category with correct amounts | API | Owner Dashboard | Positive |
| TC-S5-API-007 | Date filter ?date_from=&date_to= returns data within range only | API | Filter | Positive |
| TC-S5-API-008 | Admin cannot see data from buildings they do not manage | API | Multi-Tenant | Security |
| TC-S5-API-009 | Owner /dashboard/admin/ returns 403 | API | RBAC | Security |
| TC-S5-API-010 | Monthly trend array has 12 entries for full-year query | API | Admin Dashboard | Positive |
| TC-S5-API-011 | Building with no expenses returns 0 values (not null/error) | API | Edge Case | Positive |
| TC-S5-API-012 | Dashboard API responds within 1000ms (cached aggregations) | API | Performance | Performance |
| TC-S5-API-013 | Changing date range returns different aggregation values | API | Filter | Positive |
| TC-S5-API-014 | GET /dashboard/admin/?building_id= scopes to single building | API | Filter | Positive |
| TC-S5-API-015 | Dashboard data is consistent with /payments/ and /expenses/ endpoints | API | Data Integrity | Positive |

#### Sprint 5 — Web UI Tests (22 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S5-WEB-001 | Admin Dashboard page loads without errors | Web | Admin Dashboard | Positive |
| TC-S5-WEB-002 | Admin Dashboard shows total income summary card | Web | Admin Dashboard | Positive |
| TC-S5-WEB-003 | Admin Dashboard shows total expenses summary card | Web | Admin Dashboard | Positive |
| TC-S5-WEB-004 | Admin Dashboard shows overdue payments count card (highlighted red if > 0) | Web | Admin Dashboard | Positive |
| TC-S5-WEB-005 | Admin Dashboard shows expense trend line chart (monthly data) | Web | Admin Dashboard | Positive |
| TC-S5-WEB-006 | Trend chart has correct month labels on X axis | Web | Admin Dashboard | Positive |
| TC-S5-WEB-007 | Clicking overdue card navigates to filtered apartments list | Web | Admin Dashboard | Positive |
| TC-S5-WEB-008 | Owner Dashboard page loads without errors | Web | Owner Dashboard | Positive |
| TC-S5-WEB-009 | Owner Dashboard shows personal balance summary (owed, paid, credit) | Web | Owner Dashboard | Positive |
| TC-S5-WEB-010 | Owner Dashboard shows expense breakdown donut/pie chart by category | Web | Owner Dashboard | Positive |
| TC-S5-WEB-011 | Owner Dashboard shows recent payments list (last 5) | Web | Owner Dashboard | Positive |
| TC-S5-WEB-012 | Date range picker changes dashboard data when updated | Web | Filter | Positive |
| TC-S5-WEB-013 | Building selector on admin dashboard changes all metrics | Web | Multi-Building | Positive |
| TC-S5-WEB-014 | Charts are accessible — have aria-label or role=img | Web | Accessibility | Positive |
| TC-S5-WEB-015 | Dashboard data is consistent with what is shown in Payments list | Web | Data Integrity | Positive |
| TC-S5-WEB-016 | Download Report button triggers file download (PDF/CSV) | Web | Export | Positive |
| TC-S5-WEB-017 | Dashboard shows empty state message when no data for selected period | Web | Edge Case | Positive |
| TC-S5-WEB-018 | Owner cannot navigate to Admin Dashboard URL directly (redirects) | Web | RBAC | Security |
| TC-S5-WEB-019 | Dashboard loads within 3 seconds for typical data set | Web | Performance | Performance |
| TC-S5-WEB-020 | Hovering over chart data point shows tooltip with value | Web | Owner Dashboard | Positive |
| TC-S5-WEB-021 | Charts re-render correctly after date range change | Web | Admin Dashboard | Positive |
| TC-S5-WEB-022 | Dashboard is fully functional at 1024px (tablet) viewport | Web | Responsive | Positive |

---

### Sprint 6 — Notification System (50 Cases)

Notification accuracy is critical for owner engagement. Tests validate correct triggers, correct recipients, correct channels (email, push, in-app), and that notification preferences are respected.

*Run command: pytest -m sprint6 -v*

#### Sprint 6 — API Tests (20 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S6-API-001 | Adding a new expense triggers a notification record for each affected owner | API | Triggers | Positive |
| TC-S6-API-002 | Recording a payment triggers payment confirmation notification to owner | API | Triggers | Positive |
| TC-S6-API-003 | Scheduler job creates payment_due notification 3 days before due date | API | Scheduled | Positive |
| TC-S6-API-004 | Scheduler creates overdue notification on the day after missed due date | API | Scheduled | Positive |
| TC-S6-API-005 | GET /notifications/ returns user-scoped notification list (200) | API | Notification CRUD | Positive |
| TC-S6-API-006 | Notification list contains type, message, is_read, created_at, channel | API | Notification CRUD | Positive |
| TC-S6-API-007 | PATCH /notifications/{id}/read/ marks notification as read (is_read=true) | API | Notification CRUD | Positive |
| TC-S6-API-008 | GET /notifications/?is_read=false returns only unread notifications | API | Filter | Positive |
| TC-S6-API-009 | Notifications are scoped to the user — owner A cannot see owner B notifications | API | Multi-Tenant | Security |
| TC-S6-API-010 | Admin receives overdue notification for buildings they manage | API | Triggers | Positive |
| TC-S6-API-011 | Owner receives only notifications for their own apartment (not building-wide) | API | Multi-Tenant | Security |
| TC-S6-API-012 | Notification is not created for payment by admin on behalf (no self-notify) | API | Edge Case | Positive |
| TC-S6-API-013 | POST /notifications/preferences/ saves user channel preferences | API | Preferences | Positive |
| TC-S6-API-014 | Owner with email disabled does not receive email notification trigger | API | Preferences | Positive |
| TC-S6-API-015 | Owner with push disabled does not receive FCM push trigger | API | Preferences | Positive |
| TC-S6-API-016 | Notification logs are retained for 90 days | API | Retention | Positive |
| TC-S6-API-017 | GET /notifications/ supports pagination (default page_size=20) | API | Pagination | Positive |
| TC-S6-API-018 | Admin POST /notifications/broadcast/ sends message to all building owners | API | Broadcast | Positive |
| TC-S6-API-019 | Broadcast notification appears in each owner notification list | API | Broadcast | Positive |
| TC-S6-API-020 | Non-admin POST /notifications/broadcast/ returns 403 | API | RBAC | Security |

#### Sprint 6 — Web UI Tests (15 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S6-WEB-001 | Notification bell icon in header shows unread count badge | Web | Notification UI | Positive |
| TC-S6-WEB-002 | Clicking bell opens notification dropdown with recent notifications | Web | Notification UI | Positive |
| TC-S6-WEB-003 | Clicking a notification marks it as read and badge count decreases | Web | Notification UI | Positive |
| TC-S6-WEB-004 | View All Notifications navigates to full notification center page | Web | Notification UI | Positive |
| TC-S6-WEB-005 | Notification center shows type icon, message, date, and read/unread state | Web | Notification UI | Positive |
| TC-S6-WEB-006 | Mark All Read button clears unread badge | Web | Notification UI | Positive |
| TC-S6-WEB-007 | Overdue notification shown with red indicator | Web | Notification UI | Positive |
| TC-S6-WEB-008 | Payment confirmation notification shown with green indicator | Web | Notification UI | Positive |
| TC-S6-WEB-009 | Notification preferences page allows toggling email/push per type | Web | Preferences | Positive |
| TC-S6-WEB-010 | Saving preferences shows success toast and persists on reload | Web | Preferences | Positive |
| TC-S6-WEB-011 | Admin broadcast form has subject, message, building scope fields | Web | Broadcast | Positive |
| TC-S6-WEB-012 | Empty notification center shows helpful empty state | Web | Edge Case | Positive |
| TC-S6-WEB-013 | Notification dropdown auto-closes when clicking outside | Web | Notification UI | Positive |
| TC-S6-WEB-014 | Notification badge updates in real-time (websocket or polling) | Web | Real-time | Positive |
| TC-S6-WEB-015 | Owner notification center shows only their own notifications | Web | RBAC | Security |

#### Sprint 6 — Mobile Tests (15 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S6-MOB-001 | Push notification received when new expense created (FCM) | Mobile | Push | Mobile |
| TC-S6-MOB-002 | Push notification received 3 days before payment due | Mobile | Push | Mobile |
| TC-S6-MOB-003 | Tapping push notification opens correct screen in app | Mobile | Push | Mobile |
| TC-S6-MOB-004 | In-app notification center shows list with type, message, date | Mobile | In-App | Mobile |
| TC-S6-MOB-005 | Unread notification badge shown on notification tab icon | Mobile | In-App | Mobile |
| TC-S6-MOB-006 | Tapping notification marks it as read | Mobile | In-App | Mobile |
| TC-S6-MOB-007 | Swipe to dismiss removes notification from in-app list | Mobile | In-App | Mobile |
| TC-S6-MOB-008 | Payment confirmation push notification arrives within 60s | Mobile | Push | Mobile |
| TC-S6-MOB-009 | Push notification shows correct building name in message | Mobile | Push | Mobile |
| TC-S6-MOB-010 | User can toggle push on/off from mobile notification settings | Mobile | Preferences | Mobile |
| TC-S6-MOB-011 | Overdue notification appears in red in notification center | Mobile | In-App | Mobile |
| TC-S6-MOB-012 | Notification center is empty state friendly (not a blank screen) | Mobile | UX | Mobile |
| TC-S6-MOB-013 | Owner only sees notifications for their own apartment | Mobile | RBAC | Security |
| TC-S6-MOB-014 | App badge count (iOS) matches unread notification count | Mobile | Push | Mobile |
| TC-S6-MOB-015 | Pull-to-refresh on notification center fetches new notifications | Mobile | UX | Mobile |

---

### Sprint 7 — Flutter Mobile Finalization (38 Cases)

Sprint 7 polishes and hardenes the mobile app end-to-end. Tests focus on device compatibility, native API integration, offline handling, and app-store readiness.

*Run command: pytest -m sprint7 -v*

#### Sprint 7 — API Tests (10 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S7-API-001 | All API endpoints respond correctly to requests from mobile user-agent | API | Compatibility | Positive |
| TC-S7-API-002 | JWT refresh flow works correctly from mobile (short-lived access token) | API | Auth | Positive |
| TC-S7-API-003 | File upload endpoint handles multipart/form-data from mobile correctly | API | File Upload | Positive |
| TC-S7-API-004 | API returns 401 gracefully when mobile token expires mid-session | API | Auth | Positive |
| TC-S7-API-005 | API supports gzip compression (Accept-Encoding: gzip) from mobile | API | Performance | Positive |
| TC-S7-API-006 | Large payload responses (>100 items) paginate correctly for mobile | API | Pagination | Positive |
| TC-S7-API-007 | Network error returns proper error object (not HTML) to mobile client | API | Error Handling | Positive |
| TC-S7-API-008 | Concurrent mobile requests from same user do not produce race conditions | API | Concurrency | Positive |
| TC-S7-API-009 | API rate limit applies per-user, not per-IP (mobile behind NAT is safe) | API | Security | Security |
| TC-S7-API-010 | All API responses under 200KB for mobile bandwidth efficiency | API | Performance | Performance |

#### Sprint 7 — Mobile Tests (28 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S7-MOB-001 | App installs and launches on Android API 21 (min supported) | Mobile | Compatibility | Mobile |
| TC-S7-MOB-002 | App installs and launches on Android API 34 (latest) | Mobile | Compatibility | Mobile |
| TC-S7-MOB-003 | App installs and launches on iOS 14 (min supported) | Mobile | Compatibility | Mobile |
| TC-S7-MOB-004 | App installs and launches on iOS 17 (latest) | Mobile | Compatibility | Mobile |
| TC-S7-MOB-005 | App launches in under 3 seconds on mid-range Android device | Mobile | Performance | Performance |
| TC-S7-MOB-006 | App launches in under 3 seconds on iPhone 12 | Mobile | Performance | Performance |
| TC-S7-MOB-007 | All screens render without overflow or layout clipping | Mobile | Rendering | Mobile |
| TC-S7-MOB-008 | All screens render correctly in dark mode | Mobile | Rendering | Mobile |
| TC-S7-MOB-009 | App handles device rotation — landscape layout is usable | Mobile | Rendering | Mobile |
| TC-S7-MOB-010 | Back button behavior is consistent on Android (HW back) | Mobile | Navigation | Mobile |
| TC-S7-MOB-011 | Swipe-back gesture works on iOS | Mobile | Navigation | Mobile |
| TC-S7-MOB-012 | Camera permission request shown on first use of camera | Mobile | Permissions | Mobile |
| TC-S7-MOB-013 | App handles camera permission denial gracefully | Mobile | Permissions | Mobile |
| TC-S7-MOB-014 | Storage permission request shown on first gallery access | Mobile | Permissions | Mobile |
| TC-S7-MOB-015 | App functions correctly after permission is revoked and re-granted | Mobile | Permissions | Mobile |
| TC-S7-MOB-016 | App shows offline banner when device loses internet connection | Mobile | Offline | Mobile |
| TC-S7-MOB-017 | App resumes normally when connection restored after offline period | Mobile | Offline | Mobile |
| TC-S7-MOB-018 | Cached data shown in offline mode (last known state) | Mobile | Offline | Mobile |
| TC-S7-MOB-019 | Token refresh works correctly when app returns from background | Mobile | Auth | Mobile |
| TC-S7-MOB-020 | Session expired message shown cleanly (no crash) | Mobile | Auth | Mobile |
| TC-S7-MOB-021 | Form inputs retain state on screen rotation | Mobile | State | Mobile |
| TC-S7-MOB-022 | App does not crash on rapid navigation (stress tap test) | Mobile | Stability | Mobile |
| TC-S7-MOB-023 | Memory usage stays below 200MB after 30-minute session | Mobile | Performance | Performance |
| TC-S7-MOB-024 | No ANR (App Not Responding) during file upload on Android | Mobile | Stability | Mobile |
| TC-S7-MOB-025 | Font scales correctly with device accessibility text size settings | Mobile | Accessibility | Mobile |
| TC-S7-MOB-026 | VoiceOver (iOS) / TalkBack (Android) reads all key labels | Mobile | Accessibility | Mobile |
| TC-S7-MOB-027 | App handles incoming call during a form fill without data loss | Mobile | Interruption | Mobile |
| TC-S7-MOB-028 | APK/IPA build passes Google Play / Apple App Store checks | Mobile | Store Readiness | Mobile |

---

### Sprint 8 — Audit Logs & Data Exports (40 Cases)

Audit logs and exports are critical for financial compliance and accountability. Tests verify that all write operations are logged with correct actor, action, and timestamp, and that exports are accurate.

*Run command: pytest -m sprint8 -v*

#### Sprint 8 — API Tests (18 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S8-API-001 | Creating an expense creates an audit_log entry with action=expense.created | API | Audit Log | Positive |
| TC-S8-API-002 | Editing an expense creates an audit log entry with action=expense.updated | API | Audit Log | Positive |
| TC-S8-API-003 | Deleting an expense creates audit log with action=expense.deleted | API | Audit Log | Positive |
| TC-S8-API-004 | Recording a payment creates audit log with action=payment.recorded | API | Audit Log | Positive |
| TC-S8-API-005 | Deactivating a user creates audit log with action=user.deactivated | API | Audit Log | Positive |
| TC-S8-API-006 | Audit log entries contain user_id, action, entity, entity_id, timestamp | API | Audit Log | Positive |
| TC-S8-API-007 | Audit log user_id matches the authenticated user who performed the action | API | Audit Log | Positive |
| TC-S8-API-008 | GET /audit-logs/ is admin-only — owner returns 403 | API | RBAC | Security |
| TC-S8-API-009 | GET /audit-logs/?entity=expense lists all expense-related log entries | API | Audit Filter | Positive |
| TC-S8-API-010 | GET /audit-logs/?user_id={id} lists actions by a specific user | API | Audit Filter | Positive |
| TC-S8-API-011 | GET /exports/payments/?format=csv returns valid CSV file | API | Export | Positive |
| TC-S8-API-012 | GET /exports/payments/?format=xlsx returns valid XLSX file | API | Export | Positive |
| TC-S8-API-013 | Exported payment data matches data from GET /payments/ endpoint | API | Data Integrity | Positive |
| TC-S8-API-014 | GET /exports/expenses/?building_id= scopes export to building | API | Export | Positive |
| TC-S8-API-015 | Export with date range filter returns only data within range | API | Export | Positive |
| TC-S8-API-016 | Owner cannot access export endpoints — returns 403 | API | RBAC | Security |
| TC-S8-API-017 | PDF receipt GET /payments/{id}/receipt/ returns valid PDF | API | Receipt | Positive |
| TC-S8-API-018 | Receipt PDF contains: apartment, owner, amount, date, method, balance | API | Receipt | Positive |

#### Sprint 8 — Web UI Tests (14 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S8-WEB-001 | Admin can access Audit Log page from admin menu | Web | Audit UI | Positive |
| TC-S8-WEB-002 | Audit log table shows: timestamp, user, action, affected entity | Web | Audit UI | Positive |
| TC-S8-WEB-003 | Audit log entries are sorted newest first by default | Web | Audit UI | Positive |
| TC-S8-WEB-004 | Audit log can be filtered by user, action type, and date range | Web | Audit UI | Positive |
| TC-S8-WEB-005 | Owner cannot access Audit Log page (hidden from nav, 403 on direct access) | Web | RBAC | Security |
| TC-S8-WEB-006 | Export Payments CSV button downloads file with correct data | Web | Export | Positive |
| TC-S8-WEB-007 | Export Payments Excel button downloads XLSX file | Web | Export | Positive |
| TC-S8-WEB-008 | Export Expenses button downloads correct file | Web | Export | Positive |
| TC-S8-WEB-009 | Exported CSV includes header row with column names | Web | Export | Positive |
| TC-S8-WEB-010 | Date range selector applied before export narrows data in file | Web | Export | Positive |
| TC-S8-WEB-011 | Print Receipt button on payment record generates PDF | Web | Receipt | Positive |
| TC-S8-WEB-012 | Receipt PDF opens in new tab for preview | Web | Receipt | Positive |
| TC-S8-WEB-013 | Audit log pagination works (next/prev pages) | Web | Audit UI | Positive |
| TC-S8-WEB-014 | Export large dataset (500+ records) completes without timeout | Web | Performance | Performance |

#### Sprint 8 — Mobile Tests (8 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S8-MOB-001 | Owner can download their payment history as PDF from mobile | Mobile | Export | Mobile |
| TC-S8-MOB-002 | PDF receipt download opens in device PDF viewer | Mobile | Export | Mobile |
| TC-S8-MOB-003 | Share button on receipt allows sharing via native share sheet | Mobile | Export | Mobile |
| TC-S8-MOB-004 | Admin cannot access audit log from mobile (not in scope) | Mobile | RBAC | Security |
| TC-S8-MOB-005 | Payment receipt download works on slow connection (progress shown) | Mobile | Export | Mobile |
| TC-S8-MOB-006 | Downloaded PDF file is valid and opens without errors | Mobile | Export | Mobile |
| TC-S8-MOB-007 | Receipt contains correct owner, amount, date, and building info | Mobile | Data Integrity | Mobile |
| TC-S8-MOB-008 | Export fails gracefully with error message if server error occurs | Mobile | Error Handling | Negative |

---

### Sprint 9 — Performance & Security Hardening (35 Cases)

Sprint 9 is dedicated to non-functional quality. Performance tests use Locust to measure P95 response times under concurrent load. Security tests cover OWASP Top 10 systematically.

*Run command: pytest -m sprint9 -v*

#### Sprint 9 — Performance Tests (20 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S9-PERF-001 | GET /health/ P95 response < 200ms under 100 concurrent users | API | Performance | Performance |
| TC-S9-PERF-002 | POST /auth/login/ P95 < 500ms under 50 concurrent requests | API | Performance | Performance |
| TC-S9-PERF-003 | GET /buildings/ P95 < 500ms under 100 concurrent users | API | Performance | Performance |
| TC-S9-PERF-004 | GET /expenses/?building_id= P95 < 500ms under 100 concurrent users | API | Performance | Performance |
| TC-S9-PERF-005 | POST /payments/ P95 < 800ms under 50 concurrent users | API | Performance | Performance |
| TC-S9-PERF-006 | GET /dashboard/admin/ P95 < 1000ms (cached) under 50 users | API | Performance | Performance |
| TC-S9-PERF-007 | File upload 5MB bill image completes in < 10 seconds | API | Performance | Performance |
| TC-S9-PERF-008 | Error rate < 1% under sustained 100 req/sec load for 5 minutes | API | Performance | Performance |
| TC-S9-PERF-009 | Web login page loads in < 2 seconds (Lighthouse metric) | Web | Performance | Performance |
| TC-S9-PERF-010 | Web dashboard page loads in < 3 seconds with full data | Web | Performance | Performance |
| TC-S9-PERF-011 | Web page Lighthouse Performance score >= 70 | Web | Performance | Performance |
| TC-S9-PERF-012 | Largest Contentful Paint (LCP) < 2.5s on dashboard | Web | Performance | Performance |
| TC-S9-PERF-013 | Mobile app launch (cold start) < 3 seconds on mid-range device | Mobile | Performance | Performance |
| TC-S9-PERF-014 | Mobile list screens render in < 1.5 seconds after API response | Mobile | Performance | Performance |
| TC-S9-PERF-015 | Database query for expense split returns in < 100ms (indexed) | API | Performance | Performance |
| TC-S9-PERF-016 | Concurrent expense creation for same building does not deadlock | API | Performance | Performance |
| TC-S9-PERF-017 | Locust soak test 30 minutes at 50 users — no memory leak (stable RSS) | API | Performance | Performance |
| TC-S9-PERF-018 | GET /notifications/ for user with 1000 records paginates in < 500ms | API | Performance | Performance |
| TC-S9-PERF-019 | Balance recalculation for building with 100 apartments < 2 seconds | API | Performance | Performance |
| TC-S9-PERF-020 | Export of 5000 payment records completes in < 15 seconds | API | Performance | Performance |

#### Sprint 9 — Security Tests (15 cases)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S9-SEC-001 | OWASP A01 — Owner cannot escalate to Admin by modifying JWT role claim | API | OWASP A01 | Security |
| TC-S9-SEC-002 | OWASP A01 — Horizontal privilege: user cannot modify another user's data | API | OWASP A01 | Security |
| TC-S9-SEC-003 | OWASP A02 — All passwords are hashed (bcrypt/PBKDF2) — no plain text in DB | API | OWASP A02 | Security |
| TC-S9-SEC-004 | OWASP A02 — TLS 1.2+ enforced — TLS 1.0 and 1.1 connections rejected | API | OWASP A02 | Security |
| TC-S9-SEC-005 | OWASP A03 — SQL injection in all string inputs returns 400, not 500 | API | OWASP A03 | Security |
| TC-S9-SEC-006 | OWASP A03 — XSS payloads in all text inputs stored escaped, returned escaped | API | OWASP A03 | Security |
| TC-S9-SEC-007 | OWASP A04 — Insecure Direct Object Reference: /apartments/{id}/ enforces ownership | API | OWASP A04 | Security |
| TC-S9-SEC-008 | OWASP A04 — IDOR: /payments/{id}/ returns 403 for non-owner access | API | OWASP A04 | Security |
| TC-S9-SEC-009 | OWASP A05 — No sensitive data (passwords, tokens) in server logs | API | OWASP A05 | Security |
| TC-S9-SEC-010 | OWASP A06 — Django ALLOWED_HOSTS restricts invalid Host headers | API | OWASP A06 | Security |
| TC-S9-SEC-011 | OWASP A07 — Auth endpoint rate-limited to 10 req/min (429 after limit) | API | OWASP A07 | Security |
| TC-S9-SEC-012 | OWASP A08 — File uploads scanned for executable content (magic bytes) | API | OWASP A08 | Security |
| TC-S9-SEC-013 | OWASP A09 — 500 errors do not expose stack traces or file paths to client | API | OWASP A09 | Security |
| TC-S9-SEC-014 | OWASP A10 — SSRF: file upload URL parameter cannot be pointed at internal IP | API | OWASP A10 | Security |
| TC-S9-SEC-015 | JWT algorithm is HS256/RS256 — none algorithm rejected with 401 | API | Security | Security |

---

### Sprint 10 — Final Regression & Deployment Validation

Sprint 10 is not a new feature sprint — it is the quality gate before production release. All previous sprint tests are re-run in full. Additional production-readiness checks are performed.

*Run command: pytest -m regression -v -n auto*

#### Sprint 10 — Regression Approach

- Full regression: Run all 480+ tests across all sprints (0–9) in parallel using pytest-xdist.
- All tests must pass at 100% with 0 errors — no exceptions for production release.
- Performance benchmarks re-validated on production-equivalent infrastructure.
- Security test suite re-executed on the production deployment.
- All mobile tests executed on real physical devices (not emulators).
- End-to-end smoke suite executed post-deployment on production.

#### Sprint 10 — Production Smoke Suite (Post-Deploy)

| Test ID | Description | Layer | Category | Type |
|---|---|---|---|---|
| TC-S10-SMOKE-001 | Production /api/health/ returns 200 with status=ok | API | Smoke | Positive |
| TC-S10-SMOKE-002 | Admin can log in on production web app | Web | Smoke | Positive |
| TC-S10-SMOKE-003 | Owner can log in on production web app | Web | Smoke | Positive |
| TC-S10-SMOKE-004 | Admin can log in on production mobile app (Android) | Mobile | Smoke | Mobile |
| TC-S10-SMOKE-005 | Admin can log in on production mobile app (iOS) | Mobile | Smoke | Mobile |
| TC-S10-SMOKE-006 | Buildings list loads on production | Web | Smoke | Positive |
| TC-S10-SMOKE-007 | Creating an expense end-to-end on production | API | Smoke | Positive |
| TC-S10-SMOKE-008 | Recording a payment end-to-end on production | API | Smoke | Positive |
| TC-S10-SMOKE-009 | Push notification delivered on production (FCM) | Mobile | Smoke | Mobile |
| TC-S10-SMOKE-010 | Email notification delivered on production (SMTP) | API | Smoke | Positive |
| TC-S10-SMOKE-011 | Dashboard loads on production for admin | Web | Smoke | Positive |
| TC-S10-SMOKE-012 | Export payments CSV on production downloads valid file | Web | Smoke | Positive |
| TC-S10-SMOKE-013 | HTTPS enforced on production domain | Web | Security | Security |
| TC-S10-SMOKE-014 | API returns JSON (not HTML error pages) on production | API | Smoke | Positive |
| TC-S10-SMOKE-015 | Mobile app connects to correct production API URL | Mobile | Smoke | Mobile |

---

## 4. CI/CD Pipeline — GitHub Actions

Tests are organized into pipeline stages that run automatically. The pipeline ensures fast feedback on every commit while saving expensive tests for the right moments.

| Pipeline Stage | Tests Executed | Trigger | Est. Duration |
|---|---|---|---|
| 1. Lint & Format | flake8 + black check on all test code | Every push to any branch | < 1 minute |
| 2. Sprint 0 — Infrastructure | TC-S0-001 to TC-S0-015 (15 API tests) | Every push | ~2 minutes |
| 3. Sprint 1 — Auth API | TC-S1-API-001 to TC-S1-API-040 (40 tests) | Every push | ~5 minutes |
| 4. Sprint 1 — Auth Web | TC-S1-WEB-001 to TC-S1-WEB-025 (25 tests) | Every push | ~8 minutes |
| 5. Sprint N — Feature API | New sprint API tests (added per sprint) | Every push to sprint/* branch | ~5-10 minutes |
| 6. Sprint N — Feature Web | New sprint Web tests (added per sprint) | Every push to sprint/* branch | ~8-12 minutes |
| 7. Smoke Suite | All @smoke-marked tests (fast critical path) | Push to main only | ~3 minutes |
| 8. Mobile Tests | TC-S1-MOB through TC-S7-MOB | Every pull request | ~15-20 minutes |
| 9. Full Regression | All 480+ tests in parallel (pytest-xdist -n auto) | Nightly at 2am UTC | ~20-25 minutes |
| 10. Performance (Locust) | TC-S9-PERF-001 to TC-S9-PERF-020 | Nightly + pre-release | ~30 minutes |
| 11. Production Smoke | TC-S10-SMOKE-001 to TC-S10-SMOKE-015 | Post-deployment only | ~5 minutes |

### 4.1 Sprint Update Workflow

At the start of each sprint, the QA engineer follows this process:

- 1. Create test file: tests/api/test_sprint{N}_{feature}.py
- 2. Stub all test cases with @pytest.mark.xfail(reason="Not implemented yet")
- 3. Add @pytest.mark.sprint{N} to all new tests and register marker in pytest.ini
- 4. Commit stubs to sprint branch — developers see what will be tested
- 5. As features land, remove xfail and assert against real behavior
- 6. Sprint is not Done until 100% pass on all sprint tests
- 7. Update TEST_COVERAGE.md status and git tag: sprint-N-tests-complete

---

## 5. Tools & Technology Stack

| Category | Tool / Library | Purpose |
|---|---|---|
| Test Runner | pytest 8.1 | Core framework — markers, fixtures, plugins, reporting |
| API Testing | requests + httpx | Sync and async HTTP calls with response logging |
| Web UI | Selenium 4 + WebDriver Mgr | Browser automation with automatic driver management |
| Mobile | Appium 3 (Python client) | Flutter app automation on Android and iOS |
| Page Objects | Custom POM classes | All UI selectors isolated in page classes |
| Test Data | Faker 25 | Realistic randomized data — zero hardcoded values |
| Reports | pytest-html + Allure | HTML reports with screenshots on failure |
| Coverage | pytest-cov | Code coverage tracking per module |
| JWT | PyJWT | Inspect and validate JWT payload in security tests |
| Assertions | assertpy | Fluent assertion chaining for readable tests |
| Performance | Locust 2.29 | Load testing and P95 response time validation |
| Config | python-dotenv | Environment variable management per environment |
| CI/CD | GitHub Actions | Automated pipeline — lint, test, report on every push |
| Parallel | pytest-xdist | Parallel test execution for regression suite (-n auto) |
| Retry | pytest-rerunfailures | Auto-retry flaky tests (max 2 retries, then fail) |
| Linting | flake8 + black | Code style enforcement on all test code |

---

*— End of Document —*
