# ABEM

Apartment & Building Expense Management

# SOFTWARE REQUIREMENTS SPECIFICATION

*Web Application — Implemented Edition*

Version 3.0 | March 2026

| Document Info | Details |
|---|---|
| Status | Implemented — Web Application |
| Version | 3.0 |
| Audience | Dev / QA / Stakeholders |
| Platform | Web (React + Django REST Framework) |
| Note | This document describes the web application as fully built. The Flutter mobile application is planned for a future phase and is out of scope for this version. |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document defines the functional and non-functional requirements for the ABEM (Apartment & Building Expense Management) system. Version 3.0 reflects the web application as implemented, serving as the authoritative reference for all stakeholders throughout the ongoing development lifecycle.

### 1.2 Scope

ABEM is a multi-tenant financial management platform for managing multiple buildings, apartment units, shared expenses, and financial transactions in a transparent and organized manner. The system targets building administrators, property managers, and apartment/store owners.

#### 1.2.1 Web Application (Implemented)

Provides full administrative capabilities: system configuration, building setup, user management, expense tracking with flexible split logic, payment recording, receipt generation, dashboard analytics, in-app messaging, building asset management, data exports, and a full audit trail — all accessible via a browser.

#### 1.2.2 Mobile Application (Flutter — Future Phase)

A cross-platform (Android & iOS) application is planned for a future development phase. It will integrate with the same backend APIs as the web application.

#### 1.2.3 Backend & Infrastructure

Centralized backend built with Django + Django REST Framework (DRF), connected to a PostgreSQL database. RESTful APIs serve the web client with JWT authentication, RBAC enforcement, and multi-tenant data isolation. Celery + Redis handles asynchronous tasks and scheduled jobs.

### 1.3 Definitions, Acronyms & Abbreviations

| Term | Definition |
|---|---|
| ABEM | Apartment & Building Expense Management |
| Admin | User with full system configuration and management permissions |
| Co-Admin | Additional admin assigned to a building; same management permissions as primary admin |
| Owner | User authorized to view financial data for their assigned apartments/stores |
| Unit | An apartment or store within a building |
| API | Application Programming Interface |
| JWT | JSON Web Token — stateless authentication mechanism |
| DRF | Django REST Framework — API toolkit for Django |
| RBAC | Role-Based Access Control |
| UUID | Universally Unique Identifier |
| M2M | Many-to-Many database relationship |
| FK | Foreign Key database relationship |
| Cloudinary | Cloud-based media storage and delivery service (bill images, profile pictures) |
| ReportLab | Python PDF generation library (payment receipts) |
| drf-spectacular | Auto-generated OpenAPI 3.0 documentation for DRF APIs |
| openpyxl | Python library for reading/writing Excel (.xlsx) files |
| Celery | Distributed task queue for asynchronous and scheduled jobs |
| Split Engine | Internal service that divides an expense amount among applicable units |
| Registration Code | 8-character alphanumeric code used for owner self-registration to a specific unit |
| SRS | Software Requirements Specification |

### 1.4 Intended Audience

- Product Owners & Stakeholders
- Backend & Frontend Software Engineers
- QA Engineers & Testers
- System Architects
- DevOps & Deployment Engineers
- Project Managers

### 1.5 Assumptions & Dependencies

- Internet connectivity required for all core features.
- Cloudinary account required for media file storage (bill images, profile pictures).
- An SMTP provider is needed for email notification delivery (optional; in-app notifications work without it).
- All monetary values are handled as DECIMAL(10,2) to avoid floating-point errors.
- Expense share rounding is always upward to the nearest 5 currency units per split share, meaning the sum of shares may exceed the original expense amount.
- The base currency is Egyptian Pound (EGP); multi-currency support is not implemented.
- Payments are immutable after creation — no edits or deletions are permitted.

---

## 2. System Overview

### 2.1 System Architecture Summary

ABEM follows a layered, API-first architecture with a shared backend serving the web client. The backend is stateless and horizontally scalable.

| Layer | Technology | Responsibility |
|---|---|---|
| Data Layer | PostgreSQL 16 | Persistent storage, multi-tenant scoping, backups |
| Application Layer | Django 4.x + DRF | Business logic, REST API, authentication, RBAC |
| Task Queue | Celery + Redis 7 | Async notifications, recurring expense scheduler |
| Web Client | React 18 + Material-UI v5 | Admin & Owner web interface |
| Mobile Client | Flutter (planned) | Future phase — Android & iOS |
| File Storage | Cloudinary | Bill images, profile pictures (validated type + size) |
| PDF Generation | ReportLab | Auto-generated payment receipt PDFs |
| Auth | djangorestframework-simplejwt | JWT access + refresh token lifecycle |
| API Documentation | drf-spectacular | Auto-generated OpenAPI 3.0 schema at `/api/v1/schema/` |
| Containerization | Docker + Docker Compose | Development and deployment environment |

### 2.2 User Roles & Permissions Matrix

| Feature | Admin | Owner | Unauthenticated |
|---|---|---|---|
| Login / Logout | Full | Full | Login Only |
| Self-Register (wizard) | As Admin | As Owner | Full |
| Profile Management (name, phone, picture, password) | Full | Full | None |
| Manage Buildings (CRUD) | Full | View Own | None |
| Assign Co-Admins to Building | Full | None | None |
| Activate / Deactivate Buildings | Full | None | None |
| Manage Units (CRUD, floor, status) | Full | View Own | None |
| Invite Owner to Unit | Full | None | None |
| Claim Unit (via registration code) | Full | Full | None |
| Assign Additional Owners to Unit | Full | None | None |
| Manage Expense Categories | Full | None | None |
| Manage Expenses (CRUD) | Full | View Own Building | None |
| Upload Bill Images | Full | None | None |
| View Expense Breakdown (per-unit shares) | Full | Own Share Only | None |
| Record Payments | Full | None | None |
| View Payment History | All | Own Only | None |
| Generate & Download PDF Receipts | Full | Own Only | None |
| Admin Dashboard | Full | None | None |
| Owner Dashboard | None | Full | None |
| Manage Users (CRUD, activate/deactivate) | Full | None | None |
| Reset User Passwords | Full | None | None |
| Toggle User Messaging Restrictions | Full | None | None |
| Send In-App Messages | Full | Full (unless blocked) | None |
| Broadcast Announcements to Building | Full | None | None |
| View In-App Notifications | All | Own | None |
| Manage Building Assets | Full | None | None |
| View Audit Logs | Full | None | None |
| Export Payment / Expense Data (CSV/XLSX) | Full | None | None |

---

## 3. Feature Requirements

### 3.1 User Management

Role-based access control governs all user interactions. The system supports two primary roles: Admin and Owner.

**Authentication & Session Management:**
- JWT-based authentication with access tokens (15-minute TTL) and refresh tokens (7-day TTL).
- Automatic token refresh via interceptor in the web client; on refresh failure, user is redirected to `/401`.
- Logout blacklists the refresh token via `rest_framework_simplejwt.token_blacklist`.
- Account lockout after N consecutive failed login attempts (configurable); returns HTTP 423 with a lockout message. Successful login resets the counter.

**Self-Registration Wizard (3 paths):**
1. **Owner path** (3 steps): Account info → Select building + claim unit → Done.
2. **Admin path** (4 steps): Account info → Define buildings (name, address, city, floors, # apartments, # stores) → Optionally claim a unit → Done.
3. **Invite-code path** (3 steps): Pre-populated email from invite → Account info → Auto-claim the invited unit → Done.

**Profile Management:**
- Users can update first name, last name, phone number.
- Profile picture upload supported (JPEG, PNG, WEBP; max 5 MB; stored in Cloudinary).
- Email address is read-only after registration.
- Password change requires current password confirmation.

**Admin User Management:**
- Admin can create users directly (assigning role: admin or owner).
- Admin can activate or deactivate users (`is_active` flag; deactivated users cannot log in).
- Admin can reset any user's password without requiring the current password.
- Users list is scoped to the admin's managed buildings (users in buildings the admin administers).

**Messaging Restrictions:**
- Admin can apply two levels of restriction per user:
  - `messaging_blocked`: prevents the user from sending any messages.
  - `individual_messaging_blocked`: prevents direct (individual-target) messages only; broadcast messages still allowed if the user has them.
- Restrictions are enforced at send time on the backend.

### 3.2 Expense Management

Comprehensive expense tracking with flexible splitting logic, configurable categories, and recurring support.

**Categories:**
- Expense categories are configurable per building (not hardcoded globally).
- Each category has: Name, Description, Icon (Material icon name string), Hex Color, and an optional Parent Category (for subcategory nesting — one level deep).
- 15 default categories are automatically created when a building is created: Maintenance, Utilities, Cleaning, Security, Elevator, Plumbing, Internet & Cable, Parking, Landscaping, Pest Control, Fire Safety, Waste Management, Insurance, Management, Other.

**Expense Creation & Editing:**
- Fields: Title (required), Description, Amount (required, > 0), Expense Date (required), Due Date (optional), Category (required), Subcategory (optional), Split Type (required), Recurring toggle + Frequency.
- Admin can upload one or more bill images per expense (JPEG, PNG, PDF; max 10 MB each; stored in Cloudinary). Attachments displayed in the expense detail dialog with file size.

**Split Types (4):**
1. **Equal All Units** — expense divided equally among all apartments and stores in the building.
2. **Equal Apartments Only** — divided equally among apartment-type units only.
3. **Equal Stores Only** — divided equally among store-type units only.
4. **Custom Subset** — admin selects specific units from a checklist and optionally assigns a decimal weight per unit (e.g., 1.0 = full share, 0.5 = half share). Shares are allocated proportionally: `share_i = (weight_i / Σ weights) × total_amount`.

**Rounding Rule:** Every computed share is rounded **up** to the nearest 5 currency units (e.g., 22.01 → 25.00, 26.00 → 30.00). The total of all shares may exceed the original expense amount.

**Expense Detail View:** Shows a per-unit breakdown table with each unit's share amount and a "Shares Total" summary row.

**Recurring Expenses:**
- Admin marks an expense as recurring and sets frequency: Monthly, Quarterly, or Annual.
- A `RecurringConfig` record stores the frequency and `next_due` date.
- Celery Beat runs a daily scheduler to auto-generate the next recurrence when `next_due` is reached.

**Soft Delete:** Expenses are soft-deleted (`deleted_at` timestamp set); no records are permanently destroyed.

### 3.3 Payment Tracking

Manual payment recording by admins with full balance lifecycle management.

**Recording a Payment:**
- Admin selects the unit (dropdown showing unit number + owner name), enters the amount paid, payment date, payment method, optionally links to one or more specific expenses (multi-select) or leaves unlinked ("General Payment"), and adds notes.
- Payment recording is **atomic**: uses a database-level row lock (`SELECT FOR UPDATE`) on the apartment to prevent race conditions. `balance_before` and `balance_after` snapshots are stored on the payment record.
- Apartment running balance is updated: `balance -= amount_paid` (positive = owes, negative = credit/overpayment).
- **Payments are immutable** — no edits or deletions are permitted after creation.

**Payment Methods:** Cash, Bank Transfer, Cheque, Other (requires custom detail text if "Other" is selected).

**PDF Receipts:** Each payment generates a downloadable PDF receipt (via ReportLab) containing: Building & unit info, receipt ID (first 8 chars of UUID), amount paid, payment method, linked expense titles, balance before/after, recorder name, date, and ABEM branding. The PDF is streamed as a blob and opened in a new browser tab.

**Balance Summary Card (per unit):** Shows Total Owed (cumulative expenses), Total Paid (cumulative payments), Current Balance with a color-coded chip (Settled = green, Credit = blue, Outstanding = red).

**Payment History:** Table showing Date, Amount, Method, Notes, and Balance After for each payment.

### 3.4 Dashboards (Web)

**Owner Dashboard:**
- Balance summary card: current balance, status chip (Settled / Credit / Owed), total paid year-to-date.
- Expense breakdown donut pie chart (amounts by category).
- Recent payments table (last 5 payments): date, amount, method, notes.
- Collapsible "Claim Unit" section: owner enters an 8-character registration code to validate and claim a unit.
- Date range filter for all metrics.
- Print / Download Report button.

**Admin Dashboard:**
- Summary cards: Total Income (sum of all payments), Total Expenses (sum of all expense amounts), Overdue Accounts count (units with balance > 0) — clicking the overdue card navigates to Buildings.
- Building Summary card: total buildings, total apartments, occupied count, vacant count.
- Payment Coverage progress bar: "X of Y units settled."
- Outstanding Balances table: sortable by Unit #, Building, Owner Name, Owner Email, Balance Due.
- Monthly Income vs. Expenses bar chart (trailing 12 months).
- Filter by building and date range.
- Print / Download Report button.

### 3.5 Building & Apartment Management

**Buildings:**
- Store: Name, Address, City, Country, Number of Floors, Number of Apartments, Number of Stores.
- Primary Admin (FK) + Co-Admins (M2M) — multiple admins can manage the same building.
- Activate / Deactivate buildings; soft delete (sets `deleted_at`); admins can see inactive buildings to reactivate them, owners cannot.

**Auto-Unit Creation:**
- When a building is created (or `num_apartments` / `num_stores` is increased via edit), the system automatically generates the corresponding vacant units.
- Apartment units are numbered A01, A02, … ; store units are numbered S01, S02, …
- Units are distributed evenly across floors.
- Editing a building only appends new units — existing units are never deleted automatically.

**Units (Apartments/Stores):**
- Fields: Unit Number, Floor, Unit Type (Apartment / Store), Size (sqm, optional), Status (Occupied / Vacant / Under Maintenance).
- Multiple owners per unit: primary `owner` FK (for backward compatibility) + `owners` M2M set.
- Admin can edit floor numbers in the Manage Units dialog.

**Owner Invitation System:**
- Admin generates an invitation for a unit: enters owner's email → system creates a `UnitInvitation` with a unique link token + 8-character alphanumeric `registration_code`.
- Owner can register via the invitation link (email pre-populated) or by entering the registration code manually in the Owner Dashboard.
- Invitations have an expiry date (typically 30 days) and are single-use (`used_at` set on redemption).
- Admin can also "Claim for self" to assign themselves to a unit directly.

### 3.6 Building Asset Management

Admins track physical assets belonging to a building and record their sale.

**Asset Tracking:**
- Fields: Name (required), Description, Asset Type (Vehicle, Equipment, Furniture, Electronics, Property, Other — with custom label if Other), Acquisition Date (optional), Acquisition Value (optional).
- Assets are scoped to a building and listed in a filterable table.

**Recording a Sale:**
- Fields: Sale Date (required), Sale Price (required, > 0), Buyer Name (optional), Buyer Contact (optional), Notes (optional).
- Recording a sale marks the asset as `is_sold = True` (immutable — cannot be changed back).

**Summary Statistics:**
- Total Sale Proceeds (sum of all sale prices for the building).
- Total Assets count.

### 3.7 Notification System

**In-App Notifications:**
- In-app notification center accessible from the header bell icon with an unread count badge.
- Notifications filtered by All / Unread.
- Notification types (rendered as chips): Payment Due, Payment Overdue, Payment Confirmed, Expense Added, Expense Updated, User Registered, Announcement.
- Each notification shows type, title, body, sender (if applicable), and timestamp.
- "Mark as Read" button per unread notification.
- Automatically triggered: on expense creation (notifies all affected unit owners), on payment recording (notifies the unit owner).

**Email & Push (Production):** The notification model includes `channel` (in_app, email, push) and metadata. Actual email delivery requires SMTP credentials; push (FCM) requires Firebase configuration. Both are infrastructure-ready.

### 3.8 Communication & Messaging

**Broadcast Announcements (Admin only):**
- Admin selects a building and composes a subject + message body.
- Message is delivered as an in-app notification to all owner-role members of the building.

**Direct Messaging (All Users):**
- Any user can send a message to building members by selecting:
  - All members of the building
  - Admins only
  - Owners only
  - Specific person(s) (multi-select from building member list)
- Messaging restrictions are enforced: users with `messaging_blocked = True` cannot send any messages; users with `individual_messaging_blocked = True` cannot send to "Specific person" recipients.

### 3.9 Audit & Compliance

**Audit Log:**
- Every write operation is logged: entity type, entity ID, action (create, update, delete, activate, deactivate, login, logout, lockout, change_password, assign_user, claim, upload), the performing user, IP address, user agent, and a before/after change delta.
- Admins can view and filter the audit log by: entity type, action text, date range.
- Audit records are append-only — no edits or deletions.

**Data Exports:**
- **Payments CSV:** Date, Unit, Amount, Method, Balance Before, Balance After — filterable by apartment and date range.
- **Expenses CSV / XLSX:** ID, Building, Category, Title, Amount, Date, Split Type — filterable by building and date range. XLSX format generated via openpyxl.

---

## 4. Epics & User Stories

### Epic 1: User Management

**US-1.1: Admin User Management**
As an Admin, I want to create, edit, activate/deactivate, and reset passwords for user accounts, so that access is controlled properly.
- Acceptance: Only Admins can access user management. Deactivated users receive 401 on login.

**US-1.2: Secure Login with Lockout**
As a user, I want to log in securely; after repeated failures my account is temporarily locked.
- JWT login returns access + refresh tokens.
- After N failures: HTTP 423 with lockout expiry message.
- Acceptance: Expired tokens return HTTP 401; locked accounts return HTTP 423.

**US-1.3: Profile Management**
As a user, I want to update my name, phone, profile picture, and password on the web.
- Password change requires current password confirmation.
- Profile picture stored in Cloudinary.

**US-1.4: Self-Registration Wizard**
As a new user, I want to register myself through a multi-step wizard that guides me to set up my account and claim my unit.
- Three paths: Owner, Admin, Invite-based.
- Acceptance: Owner role is enforced for public self-registration. Admin path allows building creation.

**US-1.5: Messaging Restrictions**
As an Admin, I want to block a specific user from sending messages if they misuse the system.
- Two restriction levels: global block, individual-message block.

### Epic 2: Expense Management

**US-2.1: Create & Edit Expense**
As an Admin, I want to add categorized expenses with amount, description, date, split type, and bill attachments.

**US-2.2: Flexible Expense Splitting**
As an Admin, I want to split expenses equally among all units, apartments only, stores only, or a custom subset with optional per-unit weights.
- Acceptance: Shares rounded up to nearest 5. Unit balances updated atomically.

**US-2.3: Recurring Expenses**
As an Admin, I want to configure recurring expenses (monthly / quarterly / annual) so bills are auto-generated on schedule.

**US-2.4: Configurable Expense Categories**
As an Admin, I want to create and manage expense categories with icons, colors, and subcategories specific to each building.

**US-2.5: View Expenses (Owner)**
As an Owner, I want to view the expense list for my building and see my individual share in the expense detail breakdown.

### Epic 3: Payment Tracking

**US-3.1: Record Payment**
As an Admin, I want to manually record payments from owners, see the current balance as a guide, and have the apartment balance updated instantly.

**US-3.2: Carry-Forward Balance**
As an Admin, I want overpayments to be carried as a credit balance on the apartment, automatically reducing future dues.

**US-3.3: View Balance & History (Owner)**
As an Owner, I want to see my current outstanding balance and full payment history with balance-after snapshots.

**US-3.4: PDF Payment Receipt**
As an Admin or Owner, I want to generate and download a PDF receipt for any payment, containing all payment details and balance snapshots.

**US-3.5: Link Payment to Expenses**
As an Admin, I want to record a payment against one or more specific outstanding expenses, or record it as a general payment.

### Epic 4: Dashboards (Web)

**US-4.1: Owner Dashboard**
As an Owner, I want a graphical overview of my balance, expense breakdown by category, and recent payment history.

**US-4.2: Admin Dashboard**
As an Admin, I want a building-wide financial overview showing overdue accounts, income vs. expense trends, and a sorted list of unpaid units.

### Epic 5: Notifications & Messaging

**US-5.1: In-App Notification Center**
As a user, I want to see all my notifications in an in-app center with an unread count badge in the navigation header.

**US-5.2: Mark Notification as Read**
As a user, I want to mark individual notifications as read so I can track what I've reviewed.

**US-5.3: Broadcast Announcement**
As an Admin, I want to send an announcement to all owners of a building as an in-app notification.

**US-5.4: Direct Messaging**
As a user, I want to send a message to all members, admins, owners, or a specific person within a building.

### Epic 6: Building & Apartment Management

**US-6.1: Building Setup**
As an Admin, I want to create buildings with all relevant details (address, floors, apartment/store counts) and have vacant units auto-generated.

**US-6.2: Co-Admin Assignment**
As an Admin, I want to assign additional co-admins to a building so that management responsibility can be shared.

**US-6.3: Unit Invitation**
As an Admin, I want to invite a specific person to a unit by generating an invitation link and registration code they can use to self-register.

**US-6.4: Claim Unit by Code**
As an Owner, I want to claim a unit from my dashboard by entering the 8-character registration code given to me by my building admin.

**US-6.5: Manage Unit Details**
As an Admin, I want to edit unit floor assignments, view ownership status, and manage unit invitations from a Manage Units dialog.

### Epic 7: Building Asset Management

**US-7.1: Track Building Asset**
As an Admin, I want to record a physical building asset (vehicle, equipment, etc.) with acquisition details so the building inventory is documented.

**US-7.2: Record Asset Sale**
As an Admin, I want to record the sale of a building asset with sale price and buyer info, permanently marking it as sold.

**US-7.3: Asset Overview**
As an Admin, I want to see a list of all assets for a building with their status, acquisition value, and total sale proceeds summary.

### Epic 8: Communication & Messaging

**US-8.1: Broadcast to Building**
As an Admin, I want to send an announcement to all owners in a specific building.

**US-8.2: Message to Specific Members**
As a user, I want to send a message to a subset of building members (all, admins, owners, or specific individuals).

**US-8.3: Messaging Restriction Management**
As an Admin, I want to restrict or restore a user's ability to send messages.

### Epic 9: Audit & Data Exports

**US-9.1: View Audit Log**
As an Admin, I want to see a full audit trail of all system actions (who did what, when) filterable by entity, action, and date.

**US-9.2: Export Payment Data**
As an Admin, I want to export payment records to CSV for accounting purposes.

**US-9.3: Export Expense Data**
As an Admin, I want to export expense records to CSV or Excel (XLSX) for accounting purposes.

---

## 5. Technical Stories

**TS-1: Authentication & Authorization**
JWT-based auth with djangorestframework-simplejwt. Roles: Admin, Owner. RBAC enforced at API layer via `IsAdminRole` and `IsAuthenticated` permission classes. Account lockout implemented in `LoginView` with configurable max attempts and cooldown duration. Token blacklist on logout. Profile pictures stored in Cloudinary via ImageField.
- APIs: POST `/auth/login/`, `/auth/logout/`, `/auth/refresh/`, `/auth/register/`, `/auth/self-register/`, `/auth/change-password/`, GET/PATCH `/auth/profile/`
- JWT payload includes: user_id, role, exp
- Access token TTL: 15 minutes. Refresh token TTL: 7 days.

**TS-2: Multi-Tenant Architecture**
Tenant isolation via building membership (`UserBuilding` junction table). All querysets filter data by buildings the requesting user is a member of, admin of, or co-admin of. No middleware tenant injection — isolation is enforced per-view in `get_queryset()`.

**TS-3: Expense Engine**
Split logic engine handles four split types (equal_all, equal_apartments, equal_stores, custom). Custom split supports optional per-unit weight dictionary; proportional allocation is computed, then each share is rounded up to the nearest 5 via `round_up_to_nearest_5()`. ApartmentExpense records are created (or recalculated on edit) and apartment balances are updated. Recurring expense scheduler runs daily via Celery Beat using `RecurringConfig.next_due`. Bill attachments uploaded to Cloudinary, metadata stored in `MediaFile` polymorphic table.

**TS-4: Payment Engine**
Payment recording creates an immutable `Payment` record in an atomic transaction with `SELECT FOR UPDATE` on the apartment row. `balance_before` and `balance_after` are snapshotted. Apartment running balance is decremented. PDF receipts generated synchronously via ReportLab with Latin-1 safe encoding. Payments link to expenses via M2M through table.

**TS-5: Notification & Messaging Pipeline**
Django ORM creates `Notification` records directly for in-app delivery. `notify_expense_created()` and `notify_payment_confirmed()` are called in views after successful writes. Broadcast and direct-send endpoints enforce messaging block flags before creating notifications. Email/push channels are modeled but require SMTP/FCM credentials for actual delivery.

**TS-6: File Management**
Bill uploads validated by file type (JPEG, PNG, PDF only) and size (max 10 MB). Profile pictures validated by type (JPEG, PNG, WEBP) and size (max 5 MB). Files stored in Cloudinary via `cloudinary_storage` backend. MediaFile records track entity_type, entity_id, URL, MIME type, file size, and uploader.

**TS-7: Audit Logging**
`log_action()` utility function called throughout all write operations. Captures: user, action label, entity type, entity UUID, before/after change dict, IP address, user agent. AuditLog records are append-only (no PATCH/DELETE endpoints).

**TS-8: Data Exports**
`ExportPaymentsView` streams a CSV response with headers: ID, Apartment, Amount, Method, Date, Balance Before, Balance After.
`ExportExpensesView` supports `file_format=csv` (default) or `xlsx`; XLSX generated with openpyxl. Both views are scoped to the admin's accessible buildings.

**TS-9: Security Hardening**
HTTPS enforced (TLS 1.2+). Passwords hashed with Django's PBKDF2. JWT tokens signed with HS256. CORS configured for known origins. SQL injection prevented via Django ORM. XSS prevented via React's escaping. Secrets managed via environment variables. Refresh tokens blacklisted on logout.

**TS-10: Performance & Scalability**
Database indexes on: building_id, owner_id, expense_id, apartment_id, token (invitations). Pagination on all list endpoints (default page size: 20; clients can request up to 200 via `page_size` query param). Redis deployed for Celery broker. Dashboard queries run directly on PostgreSQL (Redis caching is a planned optimization).

**TS-11: Building Asset Management**
`BuildingAsset` and `AssetSale` models. `sell` action on `BuildingAssetViewSet` creates an `AssetSale` record and sets `is_sold=True` (enforced as immutable — no further PATCH allowed after sale). Asset list is scoped by `building_id` query param.

**TS-12: Self-Registration & Invitation System**
`UnitInvitation` model stores token (UUID), `registration_code` (8-char, auto-generated unique), invited_email, expiry, and used_at. `validate` endpoint is public (AllowAny) — returns unit/building info for the wizard UI without requiring auth. `use` endpoint is authenticated — redeems the invite, sets owner on apartment, adds user to building members.

**TS-13: CI/CD & Containerization**
Docker Compose for local development: PostgreSQL 16, Redis 7, Django backend, Celery worker, Celery Beat, React frontend (via Vite dev server). GitHub Actions workflows for linting and test automation (planned).

---

## 6. Database Schema

All tables include UUID primary keys. Multi-tenant isolation is enforced via building membership at the query layer, not via a global `tenant_id` column.

### 6.1 Core Tables

| Table | Key Fields | Relationships | Notes |
|---|---|---|---|
| users | id (UUID), email (unique), first_name, last_name, phone, profile_picture, role (admin\|owner), is_active, failed_login_attempts, locked_until, messaging_blocked, individual_messaging_blocked, notification_preferences (JSON), created_at | — | Custom auth model. USERNAME_FIELD = email. |
| buildings | id (UUID), name, address, city, country, num_floors, num_apartments, num_stores, photo, admin_id → users, is_active, deleted_at | admin → users | Primary admin FK. Co-admins via junction table. |
| building_co_admins | user_id → users, building_id → buildings, added_at | users ↔ buildings | Multiple co-admins per building. |
| user_buildings | user_id → users, building_id → buildings, joined_at | users ↔ buildings | Building membership for all users (admins + owners). |
| apartments | id (UUID), building_id → buildings, owner_id → users (nullable), unit_number, floor, unit_type (apartment\|store), size_sqm, status (occupied\|vacant\|maintenance), balance (DECIMAL 10.2) | building → buildings, owner → users | Primary owner FK + M2M owners. Balance: positive = owes, negative = credit. |
| apartment_owners | apartment_id → apartments, user_id → users | apartments ↔ users (M2M) | All owners including primary. |
| unit_invitations | id (UUID), token (UUID, unique), apartment_id → apartments, invited_email, registration_code (8 char, unique), invited_by → users, created_at, expires_at, used_at | apartment → apartments | `is_valid` property: used_at is None AND expires_at > now(). |
| expense_categories | id (UUID), building_id → buildings, name, description, icon, color (hex), parent_id → self (nullable), is_active | building → buildings, parent → self | One level of subcategory depth. Unique (building, name). |
| expenses | id (UUID), building_id → buildings, category_id → expense_categories, title, description, amount (DECIMAL 10.2), expense_date, due_date (nullable), split_type (equal_all\|equal_apartments\|equal_stores\|custom), is_recurring, deleted_at (nullable), created_by → users | building → buildings, category → expense_categories | Soft delete via deleted_at. |
| recurring_configs | id (UUID), expense_id → expenses (OneToOne), frequency (monthly\|quarterly\|annual), next_due, is_active | expense → expenses | One config per recurring expense. |
| apartment_expenses | id (UUID), apartment_id → apartments, expense_id → expenses, share_amount (DECIMAL 10.2) | apartment → apartments, expense → expenses | Unique (apartment_id, expense_id). Individual share after split + rounding. |
| payments | id (UUID), apartment_id → apartments, amount_paid (DECIMAL 10.2), payment_method (cash\|bank_transfer\|cheque\|other), payment_date, notes, balance_before (DECIMAL 10.2), balance_after (DECIMAL 10.2), recorded_by → users (nullable) | apartment → apartments | Immutable after creation. |
| payment_expenses | payment_id → payments, expense_id → expenses | payments ↔ expenses (M2M) | Links payment to zero or more expenses. |
| building_assets | id (UUID), building_id → buildings, name, description, asset_type (vehicle\|equipment\|furniture\|electronics\|property\|other), acquisition_date (nullable), acquisition_value (DECIMAL 12.2, nullable), is_sold (bool), created_by → users | building → buildings | |
| asset_sales | id (UUID), asset_id → building_assets (OneToOne), sale_date, sale_price (DECIMAL 12.2), buyer_name, buyer_contact, notes, recorded_by → users | asset → building_assets | Immutable after creation. |
| notifications | id (UUID), user_id → users, sender_id → users (nullable), notification_type, channel (in_app\|email\|push), title, body, is_read, metadata (JSON), created_at, expires_at (nullable) | user → users | User's own notifications. |
| audit_logs | id (UUID), user_id → users (nullable), action, entity, entity_id (UUID, nullable), changes (JSON), ip_address, user_agent, created_at | user → users | Append-only. |
| media_files | id (UUID), entity_type (e.g. "expense"), entity_id (UUID), url, mime_type, file_size_bytes, uploaded_by → users, created_at | polymorphic | Central media file registry. |

---

## 7. API Endpoints Reference

Base path: `/api/v1/`

### 7.1 Authentication

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| POST | `/auth/login/` | AllowAny | Email + password login → returns access + refresh tokens. Returns HTTP 423 if account locked. |
| POST | `/auth/logout/` | IsAuthenticated | Blacklists refresh token. |
| POST | `/auth/refresh/` | AllowAny | Returns new access token from refresh token. |
| POST | `/auth/register/` | IsAdminRole | Admin creates a new user (any role). |
| POST | `/auth/self-register/` | AllowAny | Public self-registration; enforces `role=owner`. |
| PATCH | `/auth/change-password/` | IsAuthenticated | Change password (requires current password). |
| GET/PATCH | `/auth/profile/` | IsAuthenticated | Retrieve or update own profile (name, phone, profile picture). |

### 7.2 Users

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/users/` | IsAdminRole | List users scoped to admin's managed buildings. Supports `?building_id=`, `?role=`, `?page_size=`. |
| GET | `/users/{id}/` | IsAdminRole | Retrieve user detail. |
| POST | `/users/` | IsAdminRole | Create user. |
| PATCH | `/users/{id}/` | IsAdminRole | Update user. |
| DELETE | `/users/{id}/` | IsAdminRole | Delete user. |
| POST | `/users/{id}/activate/` | IsAdminRole | Set `is_active=True`. |
| POST | `/users/{id}/deactivate/` | IsAdminRole | Set `is_active=False`. |
| POST | `/users/{id}/reset-password/` | IsAdminRole | Admin resets user password without current password. |
| POST | `/users/{id}/set-messaging-block/` | IsAdminRole | Set `messaging_blocked` and/or `individual_messaging_blocked` flags. |

### 7.3 Buildings

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/buildings/` | IsAuthenticated | List buildings the user can access. Supports `?page`, `?page_size`, search, ordering. |
| POST | `/buildings/` | IsAdminRole | Create building (auto-generates units + default categories). |
| GET | `/buildings/{id}/` | IsAuthenticated | Retrieve building detail. |
| PATCH | `/buildings/{id}/` | IsAdminRole | Update building (auto-appends new units if counts increased). |
| DELETE | `/buildings/{id}/` | IsAdminRole | Soft delete (sets `deleted_at` + `is_active=False`). |
| POST | `/buildings/{id}/assign-user/` | IsAdminRole | Assign an owner-role user to the building (creates UserBuilding membership). |
| POST | `/buildings/{id}/activate/` | IsAdminRole | Set `is_active=True`. |
| POST | `/buildings/{id}/deactivate/` | IsAdminRole | Set `is_active=False`. |
| GET | `/buildings/directory/` | IsAuthenticated | List active buildings the user administers or belongs to (used in sign-up wizard). |
| GET | `/buildings/{id}/apartments/` | IsAuthenticated | List units in a building. Admin sees all; owner sees own only. Supports `?page_size`. |

### 7.4 Apartments / Units

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/apartments/` | IsAuthenticated | List apartments (admin: all accessible; owner: own only). Supports `?building_id=`. |
| POST | `/apartments/` | IsAdminRole | Create apartment. |
| GET | `/apartments/{id}/` | IsAuthenticated | Retrieve apartment. |
| PATCH | `/apartments/{id}/` | IsAdminRole | Update apartment (floor, status, owner, etc.). |
| DELETE | `/apartments/{id}/` | IsAdminRole | Delete apartment. |
| GET | `/apartments/available/` | IsAuthenticated | List unowned units in a building (for sign-up wizard). `?building_id=` required. |
| POST | `/apartments/{id}/claim/` | IsAuthenticated | Authenticated user claims an unowned unit (sets owner, status=occupied). |
| POST | `/apartments/{id}/invite/` | IsAdminRole | Generate invitation token + registration code for a unit. Body: `{email}`. |
| GET | `/apartments/invite/validate/` | AllowAny | Validate invite by `?token=` or `?code=`. Returns unit/building info for registration UI. |
| POST | `/apartments/invite/use/` | IsAuthenticated | Redeem invite via `{token}` or `{code}`. Claims unit for the authenticated user. |
| GET | `/apartments/{id}/balance/` | IsAuthenticated | Balance summary for a unit (admin: any unit; owner: own only). |

### 7.5 Expenses

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/expenses/` | IsAuthenticated | List expenses. `?building_id=` required. Supports `?date_from=`, `?date_to=`, `?category_id=`. |
| POST | `/expenses/` | IsAdminRole | Create expense + trigger split engine + notify affected owners. |
| GET | `/expenses/{id}/` | IsAuthenticated | Retrieve expense with per-unit share breakdown and attachments. |
| PATCH | `/expenses/{id}/` | IsAdminRole | Update expense + recalculate splits. |
| DELETE | `/expenses/{id}/` | IsAdminRole | Soft delete expense. |
| POST | `/expenses/{id}/upload/` | IsAdminRole | Upload bill image (JPEG/PNG/PDF ≤ 10 MB) via multipart/form-data. |
| GET | `/expenses/categories/` | IsAuthenticated | List categories for a building. `?building_id=` required. |
| POST | `/expenses/categories/` | IsAdminRole | Create expense category. |
| PATCH | `/expenses/categories/{id}/` | IsAdminRole | Update expense category. |
| DELETE | `/expenses/categories/{id}/` | IsAdminRole | Soft delete category (set `is_active=False`). |

### 7.6 Payments

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/payments/` | IsAuthenticated | List payments. `?apartment_id=` recommended. Supports `?date_from=`, `?date_to=`, `?payment_method=`. |
| POST | `/payments/` | IsAdminRole | Record payment atomically. Updates apartment balance and creates balance snapshots. |
| GET | `/payments/{id}/receipt/` | IsAuthenticated | Stream PDF receipt as blob. Admin: any payment; Owner: own apartment only. |
| GET | `/payments/assets/` | IsAdminRole | List building assets. `?building_id=` required. |
| POST | `/payments/assets/` | IsAdminRole | Create building asset. |
| PATCH | `/payments/assets/{id}/` | IsAdminRole | Update building asset. |
| POST | `/payments/assets/{id}/sell/` | IsAdminRole | Record asset sale; marks asset as sold permanently. |

### 7.7 Dashboard

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/dashboard/admin/` | IsAdminRole | Admin dashboard data. Supports `?building_id=`, `?date_from=`, `?date_to=`. Returns: total_income, total_expenses, overdue_count, monthly_trend (12 months), building_summary, payment_coverage, unpaid_units. |
| GET | `/dashboard/owner/` | IsAuthenticated | Owner dashboard data. Supports `?date_from=`, `?date_to=`. Returns: balance_summary, recent_payments, expense_breakdown (by category). |

### 7.8 Notifications

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/notifications/` | IsAuthenticated | List own notifications. Supports `?is_read=true\|false`. |
| GET | `/notifications/{id}/` | IsAuthenticated | Retrieve single notification. |
| POST | `/notifications/{id}/read/` | IsAuthenticated | Mark notification as read. |
| POST | `/notifications/broadcast/` | IsAdminRole | Send announcement to all owners in a building. Body: `{building_id, title, body}`. |
| POST | `/notifications/send/` | IsAuthenticated | Send message to building members. Body: `{building_id, recipient_type, recipient_ids (optional), title, body}`. Respects messaging block flags. |

### 7.9 Audit Log

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/audit/` | IsAdminRole | List audit log entries. Supports `?entity=`, `?action=`, `?date_from=`, `?date_to=`, pagination via `?limit=` and `?offset=`. |

### 7.10 Data Exports

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| GET | `/exports/payments/` | IsAdminRole | Export payment records to CSV. Supports `?apartment_id=`, `?date_from=`, `?date_to=`. |
| GET | `/exports/expenses/` | IsAdminRole | Export expense records. Supports `?building_id=`, `?date_from=`, `?date_to=`, `?file_format=csv\|xlsx`. |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| Metric | Target | Notes |
|---|---|---|
| API Response Time (P95) | < 500ms | Under 100 concurrent users |
| Page Load Time (Web) | < 2 seconds | Measured via Lighthouse |
| File Upload (10 MB) | < 10 seconds | Via web (bill images) |
| Concurrent Users | 100+ (v1 target) | Scalable via horizontal scaling |
| Database Query (indexed) | < 50ms | With proper indexing |

Redis is deployed as the Celery broker. Direct Redis caching for dashboard aggregation queries is a planned optimization (not yet implemented — dashboards currently query PostgreSQL directly).

### 8.2 Security

- HTTPS enforced across all endpoints (TLS 1.2 minimum).
- Passwords hashed with PBKDF2 (Django default).
- JWT tokens signed with HS256; refresh tokens blacklisted on logout.
- API rate limiting configured via django-ratelimit.
- Account lockout after N failed login attempts (configurable; currently returns HTTP 423).
- File upload: type whitelist (JPEG, PNG, PDF for bills; JPEG, PNG, WEBP for profile pictures), max size enforced.
- CORS configured to allow only known frontend origins.
- All secrets stored in environment variables — never in code.
- SQL injection prevented via Django ORM parameterized queries.
- XSS prevented via React's built-in escaping.

### 8.3 Availability & Reliability

- Target uptime: 99.5% (production).
- Automated database backups: daily full backup, retained 30 days.
- Health check endpoint: `GET /api/health/` — returns system status.
- OpenAPI 3.0 documentation available at `GET /api/v1/schema/` (auto-generated by drf-spectacular).

### 8.4 Maintainability

- All APIs versioned under `/api/v1/`.
- PEP8 compliance enforced via flake8.
- API documentation auto-generated via drf-spectacular (OpenAPI 3.0).
- Data exports use openpyxl for XLSX generation.
- Docker Compose provides a reproducible local development environment.

### 8.5 Accessibility (Web)

- WCAG 2.1 Level AA compliance target.
- Keyboard navigation fully supported (MUI components).
- Color contrast ratio minimum 4.5:1.

---

## 9. Development Plan & Sprint Summary

### 9.1 Sprint Plan (As Built)

| Sprint | Focus | Key Deliverables | Status |
|---|---|---|---|
| 0 | Setup & Architecture | Docker Compose, Django project skeleton, React scaffold, PostgreSQL + Redis, CI structure | Done |
| 1 | Auth & User Management | JWT login/logout/refresh, RBAC (Admin/Owner), user CRUD, account lockout, profile management, self-registration wizard | Done |
| 2 | Buildings & Apartments | Building CRUD (with co-admins, auto-unit creation), apartment management, unit invitation + registration code flow, unit status | Done |
| 3 | Expense Management | Expense CRUD, 4 split types (including weighted custom), split engine, rounding rule, configurable categories (icon/color/subcategory), 15 default categories, bill upload (Cloudinary), recurring expenses (Celery Beat) | Done |
| 4 | Payment Management | Payment recording (atomic + balance snapshots), payment method tracking, M2M expense linking, carry-forward balance, PDF receipt (ReportLab), balance summary card | Done |
| 5 | Dashboards (Web) | Admin dashboard (income/expense/overdue cards, 12-month bar chart, outstanding balances table), Owner dashboard (balance card, donut chart, recent payments, claim-unit widget) | Done |
| 6 | Notifications & Messaging | In-app notification center (header badge, mark-as-read), expense + payment auto-notifications, broadcast announcements, direct messaging with recipient type selector, messaging restriction enforcement | Done |
| 7 | Building Asset Management | BuildingAsset + AssetSale models, asset CRUD, record-sale action, asset status, summary cards | Done |
| 8 | Audit, Exports & Security | Audit log (all write operations), audit filter UI, CSV/XLSX data exports, account lockout hardening, token blacklist on logout | Done |
| 9 | UX Polish & Bug Fixes | Form label alignment (shrink=true), PDF receipt popup-blocker fix, pagination fix (page_size param), multi-select expenses in record-payment, users scoping to admin's buildings | Done |
| 10 | Testing & QA | Unit tests (pytest), integration tests, E2E tests, load testing | Pending |
| 11 | Deployment & Launch | Production deploy, domain/TLS, monitoring (Sentry), backup configuration | Pending |
| 12 | Mobile Application (Flutter) | Native Android & iOS app using same backend APIs | Future Phase |

### 9.2 Timeline Summary

| Phase | Duration |
|---|---|
| Sprints 0–9 (Web Application) | ~18 weeks |
| Sprint 10 — Testing & QA | 2 weeks |
| Sprint 11 — Deployment | 1 week |
| Sprint 12 — Mobile (Future) | TBD |

---

## 10. Feature Implementation Status

| # | Feature | Status | Notes |
|---|---|---|---|
| 1 | JWT Authentication (login/logout/refresh) | ✅ Implemented | |
| 2 | Account lockout after failed logins (HTTP 423) | ✅ Implemented | Configurable attempts + duration |
| 3 | Self-registration wizard (Owner, Admin, Invite paths) | ✅ Implemented | |
| 4 | Profile management with picture upload | ✅ Implemented | Cloudinary storage |
| 5 | Admin user management (CRUD, activate/deactivate, reset password) | ✅ Implemented | |
| 6 | Messaging restrictions (global + individual-level) | ✅ Implemented | |
| 7 | Multi-admin buildings (primary admin + co-admins) | ✅ Implemented | |
| 8 | Auto-generation of vacant units on building creation/edit | ✅ Implemented | A01…/S01… numbering |
| 9 | Unit invitation system (email link + registration code) | ✅ Implemented | 30-day expiry, single-use |
| 10 | Multiple owners per unit (M2M) | ✅ Implemented | |
| 11 | Unit status tracking (occupied/vacant/maintenance) | ✅ Implemented | |
| 12 | Configurable expense categories (icon, color, subcategory) | ✅ Implemented | 15 defaults auto-created |
| 13 | 4 split types incl. custom weighted subset | ✅ Implemented | |
| 14 | Expense share rounding (up to nearest 5) | ✅ Implemented | |
| 15 | Bill image upload (Cloudinary, JPEG/PNG/PDF ≤ 10 MB) | ✅ Implemented | |
| 16 | Expense soft delete | ✅ Implemented | |
| 17 | Recurring expenses (monthly/quarterly/annual) | ✅ Implemented | Celery Beat scheduler |
| 18 | Expense detail view with per-unit breakdown + shares total | ✅ Implemented | |
| 19 | Payment recording (atomic, balance snapshots) | ✅ Implemented | select_for_update |
| 20 | Payment method tracking (Cash/BankTransfer/Cheque/Other) | ✅ Implemented | |
| 21 | Link payment to specific expenses (M2M) | ✅ Implemented | |
| 22 | Payment immutability (no edit/delete) | ✅ Implemented | |
| 23 | PDF payment receipt (ReportLab, browser download) | ✅ Implemented | |
| 24 | Running balance per unit (carry-forward credit) | ✅ Implemented | |
| 25 | Admin dashboard (income, expenses, overdue, chart) | ✅ Implemented | |
| 26 | Owner dashboard (balance card, pie chart, recent payments) | ✅ Implemented | |
| 27 | In-app notification center with unread badge | ✅ Implemented | |
| 28 | Broadcast announcement to building owners | ✅ Implemented | |
| 29 | Direct messaging between users with recipient type selector | ✅ Implemented | |
| 30 | Building asset management (track + record sale) | ✅ Implemented | |
| 31 | Full audit log (all write operations) | ✅ Implemented | |
| 32 | CSV/XLSX data exports (payments + expenses) | ✅ Implemented | openpyxl for XLSX |
| 33 | OpenAPI 3.0 documentation (drf-spectacular) | ✅ Implemented | `/api/v1/schema/` |
| 34 | Admin dashboard export/print report | ✅ Implemented | Browser print API |
| 35 | Claim unit by registration code from owner dashboard | ✅ Implemented | |
| 36 | Expense approval workflow | ❌ Descoped | Not in current scope |
| 37 | Bulk expense import via CSV | ❌ Descoped | Not in current scope |
| 38 | Payment due date automated email reminders | ❌ Descoped | Email delivery not configured |
| 39 | Multi-currency support | ❌ Descoped | EGP only |
| 40 | Redis caching for dashboard aggregations | 🔲 Pending | Redis deployed; caching not yet implemented |
| 41 | Notification preferences UI | 🔲 Pending | Model field exists; UI not built |
| 42 | Unit tests & integration test suite | 🔲 Pending | Sprint 10 |
| 43 | Production deployment + monitoring | 🔲 Pending | Sprint 11 |
| 44 | Flutter mobile application | 🔲 Pending | Future phase (Sprint 12+) |
| 45 | Building photo upload | 🔲 Pending | Model field exists; UI not built |
| 46 | Bulk apartment import via CSV | 🔲 Pending | |

---

*— End of Document —*
