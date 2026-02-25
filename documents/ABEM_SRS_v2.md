# ABEM

Apartment & Building Expense Management

# SOFTWARE REQUIREMENTS SPECIFICATION

*Enhanced & Comprehensive Edition*

Version 2.0 | February 2026

| Document Info | Details |
|---|---|
| Status | Enhanced Draft |
| Version | 2.0 |
| Audience | Dev / QA / Stakeholders |
| Platforms | Web + Mobile (Flutter) |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document defines the functional and non-functional requirements for the ABEM (Apartment & Building Expense Management) system, comprising a Web Application and a Flutter-based Mobile Application.

This document serves as the authoritative reference for all stakeholders throughout the software development lifecycle, covering system behavior, user roles, data flows, constraints, security, and deployment strategy.

### 1.2 Scope

ABEM is a multi-tenant financial management platform designed to manage multiple buildings, apartment units, shared expenses, and financial transactions in a transparent and organized manner. The system targets building administrators, property managers, and apartment owners/tenants.

#### 1.2.1 Web Application

Provides full administrative capabilities: system configuration, building setup, financial tracking, reporting, dashboards, and operational management via a browser.

#### 1.2.2 Mobile Application (Flutter)

Cross-platform (Android & iOS) application for administrators and owners. Supports all operational features except the dashboard module. Integrates with the same backend APIs as the web application.

#### 1.2.3 Backend & Infrastructure

Centralized backend built with Django + Django REST Framework (DRF), connected to a PostgreSQL database. RESTful APIs serve both web and mobile clients with JWT authentication, RBAC enforcement, and multi-tenant data isolation.

### 1.3 Definitions, Acronyms & Abbreviations

| Term | Definition |
|---|---|
| ABEM | Apartment & Building Expense Management |
| Admin | User with full system configuration and management permissions |
| Owner | User authorized to view financial data for their assigned apartments |
| Tenant | Physical occupant of an apartment unit (may differ from Owner) |
| API | Application Programming Interface |
| JWT | JSON Web Token — stateless authentication mechanism |
| DRF | Django REST Framework — API toolkit for Django |
| RBAC | Role-Based Access Control |
| FCM | Firebase Cloud Messaging — push notification service |
| RLS | Row-Level Security — PostgreSQL feature for data isolation |
| SRS | Software Requirements Specification |
| CI/CD | Continuous Integration / Continuous Deployment |
| UUID | Universally Unique Identifier |

### 1.4 Intended Audience

- Product Owners & Stakeholders
- Backend & Frontend/Mobile Software Engineers
- QA Engineers & Testers
- System Architects
- DevOps & Deployment Engineers
- Project Managers

### 1.5 Assumptions & Dependencies

- Internet connectivity required for all core features (no full offline mode in v1).
- Firebase account required for push notification functionality.
- An SMTP provider (e.g., SendGrid, Gmail SMTP) is needed for email notifications.
- App Store / Google Play Developer accounts required for mobile distribution.
- All monetary values are handled as DECIMAL(10,2) to avoid floating-point errors.
- Rounding of expense splits is always upward to the nearest 5 units of currency.

---

## 2. System Overview

### 2.1 System Architecture Summary

ABEM follows a layered, API-first architecture with a shared backend serving multiple frontend clients. The backend is stateless and horizontally scalable.

| Layer | Technology | Responsibility |
|---|---|---|
| Data Layer | PostgreSQL 15+ | Persistent storage, RLS, backups |
| Application Layer | Django 4.x + DRF | Business logic, API, auth, multi-tenancy |
| Web Client | React.js + Material-UI | Admin & Owner web interface |
| Mobile Client | Flutter (Dart) | Android & iOS app |
| Notifications | SMTP + Firebase FCM | Email and push notifications |
| Auth | JWT (djangorestframework-simplejwt) | Token-based authentication |
| File Storage | AWS S3 / Cloudinary | Bill images and media uploads |
| DevOps | GitHub Actions + Docker | CI/CD pipeline |

### 2.2 User Roles & Permissions Matrix

| Feature | Admin | Owner | Unauthenticated |
|---|---|---|---|
| Login / Logout | Full | Full | Login Only |
| Manage Buildings | Full CRUD | View Own | None |
| Manage Apartments | Full CRUD | View Own | None |
| Manage Expenses | Full CRUD | View Only | None |
| Record Payments | Full | None | None |
| View Payment History | All | Own Only | None |
| Admin Dashboard (Web) | Full | None | None |
| Owner Dashboard (Web) | Full | Own | None |
| Upload Bill Images | Full | None | None |
| Manage Notifications | Full | Own | None |
| Manage Users | Full | None | None |
| View Audit Logs | Full | None | None |

---

## 3. Feature Requirements

### 3.1 User Management

Role-based access control governs all user interactions. The system supports two primary roles: Admin and Owner.

- Admins: Can manage multiple buildings, all financial operations, all users, and all data.
- Owners: Can view and track balances only for buildings and apartments they are assigned to.
- JWT-based authentication shared across Web and Mobile platforms.
- Profile management (name, email, phone, password) available on both platforms.
- Session management with secure token refresh and revocation on logout.
- Mobile: Secure token storage using flutter_secure_storage package.
- Mobile: Role-based UI rendering — screens and actions adapt to user role.
- [ENHANCEMENT] Account lockout after 5 consecutive failed login attempts with cooldown.
- [ENHANCEMENT] Password complexity policy enforcement (min 8 chars, uppercase, number, special char).
- [ENHANCEMENT] Admin audit log for all user management actions.

### 3.2 Expense Management

Comprehensive expense tracking with flexible splitting logic and recurring support.

- Add and categorize expenses: water, electricity, maintenance, elevator, cleaning, security, etc.
- Define recurring expenses (monthly, quarterly, annual) with automatic generation via scheduled jobs.
- Split expenses equally among all apartments/stores, or by unit type (apartments only, stores only, or custom subsets).
- Automatic rounding of individual shares upward to the nearest 5 currency units.
- Track full expense history per building with filters by date, category, and status.
- Upload bill images via device camera or gallery (Mobile) or file upload (Web).
- [ENHANCEMENT] Expense approval workflow: Admin creates expense, Super-Admin reviews (optional).
- [ENHANCEMENT] Expense categories are configurable per building (not hardcoded).
- [ENHANCEMENT] Bulk expense import via CSV upload.
- [ENHANCEMENT] Soft delete for expenses — no permanent data loss.
- [ENHANCEMENT] Expense version history (audit trail of edits).

### 3.3 Payment Tracking

Manual and semi-automated payment recording with full balance management.

- Manual payment recording by Admins via Web and Mobile.
- Support for partial payments, exact payments, and overpayments.
- Carry-forward balance logic: overpaid amounts auto-credited to next due.
- Automatic balance recalculation per apartment/store after each transaction.
- Full payment history with date, amount, related expense, and balance snapshot.
- [ENHANCEMENT] Payment receipts — auto-generate a PDF receipt per recorded payment.
- [ENHANCEMENT] Payment method tracking (cash, bank transfer, cheque, etc.).
- [ENHANCEMENT] Payment due date enforcement with automated reminders before due date.
- [ENHANCEMENT] Multi-currency support with exchange rate configuration (future phase).

### 3.4 Dashboard (Web Only)

**Owner Dashboard**

- Personal balance summary (current outstanding, total paid year-to-date).
- Recent payments overview with pagination.
- Expense breakdown by category (pie/donut chart).
- Payment trend graph (monthly bar chart).
- [ENHANCEMENT] Download dashboard summary as PDF report.

**Admin Dashboard**

- Overdue payment monitoring with apartment-level drill-down.
- Expense analytics and trends (line chart by month/category).
- Building-level financial health indicators.
- Total income vs. total expenses summary cards.
- [ENHANCEMENT] Configurable date ranges for all dashboard metrics.
- [ENHANCEMENT] Export data to Excel/CSV from dashboard.

### 3.5 Building & Apartment Management

- Store and manage: building name, address, number of floors, apartments, and stores.
- Define per-apartment expense participation rules (which expense categories apply to each unit).
- Apartment-specific data: owner name, unit size (sqm), floor number, unit type (apartment/store).
- Multi-building support: single admin can manage unlimited buildings.
- Search and filtering for buildings and units on both platforms.
- [ENHANCEMENT] Building photo upload for identification.
- [ENHANCEMENT] Floor plan or map view (future phase).
- [ENHANCEMENT] Apartment status tracking (occupied, vacant, under maintenance).
- [ENHANCEMENT] Bulk apartment creation via CSV import.

### 3.6 Notification System

Multi-channel notifications triggered by system events.

| Event | Email | Push (Mobile) | In-App | Recipient |
|---|---|---|---|---|
| Payment Due (3 days before) | Yes | Yes | Yes | Owner |
| Payment Due (day of) | Yes | Yes | Yes | Owner |
| Payment Overdue | Yes | Yes | Yes | Owner + Admin |
| New Expense Added | Yes | Yes | Yes | All Owners |
| Payment Confirmed | Yes | Yes | Yes | Owner |
| Expense Updated | Yes | Yes | Yes | Affected Owners |
| New User Registered | Yes | No | No | Admin |

- [ENHANCEMENT] Notification preferences: Users can choose which notification types they receive.
- [ENHANCEMENT] Notification history stored for 90 days.
- [ENHANCEMENT] Admin can broadcast announcements to all owners of a building.

---

## 4. Epics & User Stories

### Epic 1: User Management

**US-1.1: Admin User Management**

As an Admin, I want to create, edit, deactivate, and assign roles to user accounts, so that access is controlled properly.

- Web: Full CRUD for users, role assignment, activation/deactivation, password reset.
- Mobile: View user list; limited management based on permission level.
- Acceptance: Only Admins can access user management. Deactivated users cannot log in.

**US-1.2: Secure Login**

As a user, I want to log in securely and see only buildings and apartments I am authorized to access.

- JWT-based login returning access token + refresh token.
- Mobile: Tokens stored in flutter_secure_storage. Refresh on expiry.
- Acceptance: Unauthorized API endpoints return HTTP 403. Expired tokens return HTTP 401.

**US-1.3: Profile Management**

As a user, I want to update my profile (name, phone, email, password) on both web and mobile.

- Password change requires current password confirmation.
- Email change triggers re-verification.

### Epic 2: Expense Management

**US-2.1: Create Expense**

As an Admin, I want to add categorized expenses with amount, description, date, and bill image attachment.

**US-2.2: Recurring Expenses**

As an Admin, I want to configure recurring expenses with frequency settings so bills are auto-generated.

**US-2.3: Expense Splitting**

As an Admin, I want to split expenses equally or by type so each unit pays its fair share.

**US-2.4: View Expenses (Owner)**

As an Owner, I want to view my expense breakdown by month and category so I understand what I owe.

### Epic 3: Payment Tracking

**US-3.1: Record Payment**

As an Admin, I want to manually record payments from owners and update balances instantly.

**US-3.2: Overpayment Handling**

As an Admin, I want the system to carry forward overpayments to reduce future dues automatically.

**US-3.3: View Balance (Owner)**

As an Owner, I want to see my current outstanding balance and full payment history on web and mobile.

### Epic 4: Dashboards (Web Only)

**US-4.1: Owner Dashboard**

As an Owner, I want a graphical overview of my financial position for the current building.

**US-4.2: Admin Dashboard**

As an Admin, I want a building-wide financial overview with overdue accounts highlighted.

### Epic 5: Notifications

**US-5.1: Payment Reminders**

As an Owner, I want to receive email and push notifications before and on my payment due dates.

**US-5.2: Overdue Alerts**

As an Admin, I want push and email alerts for overdue payments so I can follow up.

### Epic 6: Building & Apartment Management

**US-6.1: Building Setup**

As an Admin, I want to create buildings with all relevant details and manage their apartment units.

**US-6.2: Owner Assignment**

As an Admin, I want to assign owners to apartments so billing and notifications are properly linked.

### Epic 7: Audit & Compliance [ENHANCEMENT]

**US-7.1: Audit Log**

As an Admin, I want to see a full audit log of all system actions (who did what, when) for accountability.

**US-7.2: Data Export**

As an Admin, I want to export expense and payment reports to Excel/PDF for accounting purposes.

---

## 5. Technical Stories

**TS-1: Authentication & Authorization**

Implement JWT-based auth with djangorestframework-simplejwt. Roles: Admin, Owner. RBAC enforced at API layer. Flutter uses flutter_secure_storage for token persistence. All endpoints require HTTPS.

- APIs: POST /auth/login, POST /auth/logout, POST /auth/refresh, POST /auth/register, POST /auth/change-password
- JWT payload includes: user_id, role, tenant_ids, exp
- Access token TTL: 15 minutes. Refresh token TTL: 7 days.
- [ENHANCEMENT] Rate limiting: 5 failed login attempts triggers 15-minute lockout.

**TS-2: Multi-Tenant Architecture**

Shared schema model with tenant_id (UUID) scoping all data per building. Middleware injects tenant context from JWT. All querysets auto-filter by tenant. Optional PostgreSQL RLS as additional isolation layer.

**TS-3: Expense Engine**

Split logic engine handles equal splits and type-based splits. Rounding always up to nearest 5. Recurring expense scheduler runs daily via Celery Beat. Bill attachments stored in S3/Cloudinary.

**TS-4: Payment Engine**

Payment recording creates ledger entries. Partial/over payment logic recalculates running balance. Carry-forward auto-applied at next expense assignment. All calculations use Python Decimal type.

**TS-5: Notification Pipeline**

Django signals trigger notification events. Celery workers process async email (SMTP) and push (FCM) delivery. Notification records stored in DB for in-app center. Celery Beat runs scheduled reminders (3 days before due, day of due, day after due).

**TS-6: File Management**

Bill image uploads validated by file type (JPEG, PNG, PDF only) and size (max 10MB). Files stored in cloud object storage with pre-signed URLs for access. Mobile: uses image_picker Flutter package for camera/gallery access.

**TS-7: Flutter Mobile App**

Single Dart/Flutter codebase targeting Android (API 21+) and iOS (14+). Uses: dio for HTTP, flutter_secure_storage for tokens, firebase_messaging for push, image_picker for camera/gallery. Implements BLoC or Provider pattern for state management.

**TS-8: CI/CD Pipeline**

GitHub Actions workflows for: linting (flake8 + dart analyze), unit tests (pytest + flutter test), Docker build, deployment to staging. Flutter builds via Fastlane for store submission.

**TS-9: Security Hardening**

HTTPS enforced (TLS 1.2+). Passwords hashed with PBKDF2/Bcrypt. File upload validation (type + size + virus scan). API rate limiting with django-ratelimit. Audit logs for all write operations. Secrets managed via environment variables.

**TS-10: Performance & Scalability**

Database indexes on tenant_id, apartment_id, user_id, date fields. Pagination on all list endpoints (default page size: 20). API response caching with Redis for dashboard aggregations. Target: API P95 response < 500ms under 100 concurrent users.

---

## 6. Database Schema (Optimized)

All tables include tenant_id (UUID) for multi-tenant isolation. Schema uses PostgreSQL-native types and constraints. Below is the complete, enhanced schema.

### 6.1 Core Tables

| Table | Key Fields | Relationships | Notes |
|---|---|---|---|
| users | id, email, role, password_hash | — | Role: Admin \| Owner. Unique email. |
| buildings | id, name, tenant_id, admin_id | admin_id → users | tenant_id is building UUID. One admin per building. |
| apartments | id, building_id, owner_id, type | building_id → buildings, owner_id → users | type: Apartment \| Store. Includes balance field. |
| expense_categories | id, building_id, name | building_id → buildings | [NEW] Configurable per building. Replaces hardcoded categories. |
| expenses | id, building_id, category_id, amount, is_recurring | building_id → buildings, category_id → expense_categories | Includes soft_delete_at field. |
| recurring_configs | id, expense_id, frequency, next_due | expense_id → expenses | [NEW] Separate table for recurring logic. |
| apartment_expenses | id, apartment_id, expense_id, share_amount | apartment_id → apartments, expense_id → expenses | Stores individual share after split + rounding. |
| payments | id, apartment_id, expense_id, amount_paid, method | apartment_id → apartments, expense_id → expenses | [ENHANCED] Added payment_method field. |
| notifications | id, user_id, type, is_read, channel | user_id → users | [ENHANCED] Added channel (email/push/in-app). |
| audit_logs | id, user_id, action, entity, entity_id | user_id → users | [NEW] Full audit trail for all write operations. |
| user_buildings | user_id, building_id | users ↔ buildings (M2M) | [NEW] Explicit junction table for multi-building access. |
| media_files | id, entity_type, entity_id, url, mime_type | Polymorphic | [NEW] Central media file registry for bill images. |

---

## 7. API Endpoints Reference

### 7.1 Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/v1/auth/login/ | None | Returns access + refresh tokens |
| POST | /api/v1/auth/refresh/ | Refresh Token | Returns new access token |
| POST | /api/v1/auth/logout/ | JWT | Blacklists refresh token |
| PATCH | /api/v1/auth/change-password/ | JWT | Update user password |

### 7.2 Buildings

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/v1/buildings/ | JWT | List all buildings (Admin: all; Owner: assigned) |
| POST | /api/v1/buildings/ | Admin | Create new building |
| GET | /api/v1/buildings/{id}/ | JWT | Get building details |
| PATCH | /api/v1/buildings/{id}/ | Admin | Update building |
| DELETE | /api/v1/buildings/{id}/ | Admin | Soft delete building |

### 7.3 Expenses

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/v1/expenses/?building_id= | JWT | List expenses for a building |
| POST | /api/v1/expenses/ | Admin | Create new expense + trigger split |
| GET | /api/v1/expenses/{id}/ | JWT | Get expense details + shares |
| PATCH | /api/v1/expenses/{id}/ | Admin | Update expense (creates audit entry) |
| DELETE | /api/v1/expenses/{id}/ | Admin | Soft delete expense |
| POST | /api/v1/expenses/{id}/upload/ | Admin | Upload bill image attachment |

### 7.4 Payments

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | /api/v1/payments/?apartment_id= | JWT | List payment history (scoped) |
| POST | /api/v1/payments/ | Admin | Record payment + recalculate balance |
| GET | /api/v1/payments/{id}/ | JWT | Get payment details |
| GET | /api/v1/apartments/{id}/balance/ | JWT | Current balance for an apartment |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| Metric | Target | Notes |
|---|---|---|
| API Response Time (P95) | < 500ms | Under 100 concurrent users |
| Page Load Time (Web) | < 2 seconds | Measured via Lighthouse |
| Mobile App Launch | < 3 seconds (cold) | After first launch |
| File Upload (10MB) | < 10 seconds | Via mobile or web |
| Concurrent Users | 100+ (v1 target) | Scalable via horizontal scaling |
| Database Query (indexed) | < 50ms | With proper indexing |

### 8.2 Security

- HTTPS enforced across all endpoints (TLS 1.2 minimum).
- Passwords hashed with PBKDF2 (Django default) or Bcrypt (configurable).
- JWT tokens signed with RS256 (asymmetric) or HS256 (symmetric minimum).
- API rate limiting: 100 req/min per authenticated user; 10 req/min for auth endpoints.
- File upload: type whitelist (JPEG, PNG, PDF), max 10MB, malware scan (optional).
- CORS configured to allow only known frontend origins.
- All secrets (DB passwords, API keys) stored in environment variables — never in code.
- SQL injection prevented via Django ORM parameterized queries.
- XSS prevented via React's built-in escaping; Content-Security-Policy headers.
- [ENHANCEMENT] OWASP Top 10 security checklist completed before production launch.

### 8.3 Availability & Reliability

- Target uptime: 99.5% (production).
- Automated database backups: daily full backup, retained 30 days.
- Backup stored in separate cloud region.
- Health check endpoint: GET /api/health/ — returns system status.
- Error tracking via Sentry (Web + Mobile).

### 8.4 Maintainability

- Code coverage target: minimum 70% for backend unit tests.
- All APIs versioned under /api/v1/ to allow non-breaking future changes.
- PEP8 compliance enforced via flake8 in CI pipeline.
- Dart/Flutter code analyzed via dart analyze + flutter_lints.
- API documentation auto-generated via drf-spectacular (OpenAPI 3.0).

### 8.5 Accessibility (Web)

- WCAG 2.1 Level AA compliance target.
- Keyboard navigation fully supported.
- Screen reader compatible semantic HTML.
- Color contrast ratio minimum 4.5:1.

---

## 9. Development Plan & Milestones

### 9.1 Sprint Plan

| Sprint | Focus | Key Deliverables | Duration |
|---|---|---|---|
| 0 | Setup & Architecture | Repo, CI/CD, DB schema, Django project skeleton, Flutter scaffold | 1 week |
| 1 | Auth & User Mgmt | JWT auth, RBAC, user APIs, Flutter auth screens, secure storage | 2 weeks |
| 2 | Buildings & Apartments | Building/Apartment CRUD APIs, Web UI, Flutter screens | 2 weeks |
| 3 | Expense Management | Expense APIs, split engine, recurring scheduler, file upload, Flutter UI | 2 weeks |
| 4 | Payment Management | Payment APIs, balance engine, carry-forward logic, Flutter UI | 2 weeks |
| 5 | Dashboards (Web) | Owner & Admin dashboards, chart components, aggregation APIs | 1.5 weeks |
| 6 | Notifications | Email (SMTP), FCM push, in-app center, scheduled reminders | 1.5 weeks |
| 7 | Flutter Finalization | UX polish, role-based rendering, offline token, device testing | 1.5 weeks |
| 8 | Audit & Exports | Audit log, PDF/Excel export, notification preferences | 1 week |
| 9 | Testing & QA | Unit, integration, E2E, mobile device testing, load testing | 2 weeks |
| 10 | Deployment & Launch | Production deploy, Play Store / App Store, beta release | 1 week |

### 9.2 Timeline Summary

| Phase | Duration |
|---|---|
| Requirements & Design | 2–3 weeks |
| Development (Sprints 0–8) | 14–15 weeks |
| Testing & QA | 2 weeks |
| Deployment | 1 week |
| **TOTAL** | **19–21 weeks (~5 months)** |

---

## 10. Enhancements & Gaps Addressed

The following items were identified as missing or underspecified in the original SRS and have been added in this enhanced version:

| # | Enhancement | Category |
|---|---|---|
| 1 | Account lockout after failed logins | Security |
| 2 | Password complexity policy | Security |
| 3 | Configurable expense categories per building | Functionality |
| 4 | Expense soft delete (no data loss) | Data Integrity |
| 5 | Expense audit trail / version history | Compliance |
| 6 | Payment method field (cash/transfer/cheque) | Functionality |
| 7 | PDF payment receipts | UX / Accounting |
| 8 | Full audit log table (who did what, when) | Compliance |
| 9 | Data export to Excel/CSV/PDF | Reporting |
| 10 | Notification preferences per user | UX |
| 11 | Admin broadcast announcements to owners | Communication |
| 12 | user_buildings junction table for explicit M2M | Data Model |
| 13 | recurring_configs separate table | Data Model |
| 14 | media_files central registry | Data Model |
| 15 | Apartment status (occupied/vacant) | Functionality |
| 16 | Bulk import via CSV | Admin UX |
| 17 | API versioning (/api/v1/) | Architecture |
| 18 | OpenAPI 3.0 docs (drf-spectacular) | DX / Documentation |
| 19 | Redis caching for dashboard aggregations | Performance |
| 20 | OWASP Top 10 security checklist | Security |
| 21 | WCAG 2.1 AA accessibility compliance (Web) | Accessibility |
| 22 | Health check endpoint | Ops / Monitoring |
| 23 | Roles & Permissions matrix | Documentation |
| 24 | Complete API endpoint reference table | Documentation |
| 25 | Non-functional requirements with measurable targets | Documentation |

---

*— End of Document —*
