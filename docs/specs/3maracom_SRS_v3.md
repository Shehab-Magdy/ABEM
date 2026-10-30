# عِمارة.كوم (3maracom)

Owners' Association & Building Expense Management — formerly ABEM

# SOFTWARE REQUIREMENTS SPECIFICATION

*Web Application — Implemented Edition*

Version 3.3 | October 2026

| Document Info | Details |
|---|---|
| Status | Implemented — Web Application |
| Version | 3.3 |
| Audience | Dev / QA / Stakeholders |
| Platform | Web and installable PWA for Android and iOS (React + Django REST Framework) |
| Note | This document describes the web application as fully built. Android and iOS are served by the web application as an installable Progressive Web App (PWA); native Flutter apps were dropped. |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document defines the functional and non-functional requirements for the عِمارة.كوم (3maracom, formerly ABEM) system. Version 3.2 reflects the web application and its installable PWA as implemented, serving as the authoritative reference for all stakeholders throughout the ongoing development lifecycle.

### 1.2 Scope

عِمارة.كوم (3maracom) is an Arabic-first, multi-tenant financial management platform for owners' associations (اتحاد الملاك) and residents in Egypt and the Arab world for managing multiple buildings, apartment units, shared expenses, and financial transactions in a transparent and organized manner. The system targets building administrators, property managers, and apartment/store owners.

#### 1.2.1 Web Application (Implemented)

Provides full administrative capabilities: system configuration, building setup, user management, expense tracking with flexible split logic, payment recording, receipt generation, dashboard analytics, in-app messaging, building asset management, data exports, and a full audit trail — all accessible via a browser.

#### 1.2.2 Mobile Experience (Installable PWA — Planned)

Android and iOS users will use the same React web application, installed from the browser as a Progressive Web App (web manifest, service worker, responsive and RTL layout). It uses the same backend APIs; no separate native codebase is maintained. Installability, offline behavior and push support on iOS are subject to platform limits and are validated on real devices.

#### 1.2.3 Backend & Infrastructure

Centralized backend built with Django + Django REST Framework (DRF), connected to a PostgreSQL database. RESTful APIs serve the web client with JWT authentication, RBAC enforcement, and multi-tenant data isolation. A daily management command (run by the host scheduler) handles scheduled jobs; notifications are sent while the request is handled.

### 1.3 Definitions, Acronyms & Abbreviations

| Term | Definition |
|---|---|
| 3maracom / عِمارة.كوم | Product name (formerly ABEM — Apartment & Building Expense Management) |
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

3maracom follows a layered, API-first architecture with a shared backend serving the web client. The backend is stateless and horizontally scalable.

| Layer | Technology | Responsibility |
|---|---|---|
| Data Layer | PostgreSQL 16 | Persistent storage, multi-tenant scoping, backups |
| Application Layer | Django 4.x + DRF | Business logic, REST API, authentication, RBAC |
| Scheduled jobs | Django management command (host cron) | Daily recurring-expense generation; no Celery or Redis |
| Web Client | React 18 + Material-UI v5 | Admin & Owner web interface |
| Mobile Client | Installable PWA (React web app) | Planned — Android & iOS via browser install |
| File Storage | Cloudinary | Bill images, profile pictures (validated type + size) |
| PDF Generation | ReportLab | Auto-generated payment receipt PDFs |
| Auth | djangorestframework-simplejwt | JWT access + refresh token lifecycle |
| API Documentation | drf-spectacular | Auto-generated OpenAPI 3.0 schema at `/api/schema/` |
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
- A daily management command (`generate_recurring_expenses`, run by the host scheduler) copies each due recurring expense as a normal expense dated on `next_due`, splits it like the original, advances `next_due`, and catches up on missed periods.

**Soft Delete:** Expenses are soft-deleted (`deleted_at` timestamp set); no records are permanently destroyed.

### 3.3 Payment Tracking

Manual payment recording by admins with full balance lifecycle management.

**Recording a Payment:**
- Admin selects the unit (dropdown showing unit number + owner name), enters the amount paid, payment date, payment method, optionally links to one or more specific expenses (multi-select) or leaves unlinked ("General Payment"), and adds notes.
- Payment recording is **atomic**: uses a database-level row lock (`SELECT FOR UPDATE`) on the apartment to prevent race conditions. `balance_before` and `balance_after` snapshots are stored on the payment record.
- Apartment running balance is updated: `balance -= amount_paid` (positive = owes, negative = credit/overpayment).
- **Payments are immutable** — no edits or deletions are permitted after creation.

**Payment Methods:** Cash, Bank Transfer, Cheque, Mobile Wallet, InstaPay, Other (requires custom detail text if "Other" is selected).

**PDF Receipts:** Each payment generates a downloadable PDF receipt (via WeasyPrint) in A6 page format, bilingual (Arabic/English) containing: Building info, unit number + first owner's full name, receipt ID (first 8 chars of UUID), amount paid, payment method, linked expense titles, balance before/after, recorder's full name (no email), date, and عِمارة.كوم | 3mara.com branding. The PDF is streamed as a blob and opened in a new browser tab.

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
- Multiple owners per unit: primary `owner` FK (for backward compatibility) + `owners` M2M set. Up to any number of co-owners may be assigned.
- Admin can edit floor numbers in the Manage Units dialog.
- The Manage Units dialog displays all current owner names above the invite form, and includes an "Invite another" button to generate additional invitations for already-occupied units.

**Owner Invitation System:**
- Admin generates an invitation for a unit: enters owner's email → system creates a `UnitInvitation` with a unique link token + 8-character alphanumeric `registration_code`.
- Owner can register via the invitation link (email pre-populated) or by entering the registration code manually in the Owner Dashboard.
- Invitations have an expiry date (typically 30 days) and are single-use (`used_at` set on redemption).
- **Multiple owners:** inviting a new owner to an already-occupied unit does not replace the existing owner. The new user is added to the `owners` M2M set; the primary `owner` FK is set only on the first claim and never overwritten. A user already in the `owners` set cannot claim the same unit again (HTTP 409).
- Admin can also "Claim for self" to assign themselves to a unit directly (only shown when the unit has no owner yet).

**Shared Unit Data Visibility:**

- All owners of the same unit (whether primary or co-owner) see identical data: the same payment history, balance summary, and owner dashboard figures. Payment and dashboard queries use `Q(apartment__owner=user) | Q(apartment__owners=user)` to include all co-owned units.

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

**Notification Center Page Layout:**

- The page is organized into three independently collapsible accordion panels, each with a colored accent header (icon, title, unread badge, expand/collapse chevron):
  1. **Send Message** (indigo) — compose panel, collapsed by default.
  2. **Broadcast Announcement** (amber, admin only) — compose panel, collapsed by default.
  3. **Your Notifications** (green) — notifications list with filter chips, expanded by default.
- The two compose panels sit side by side at the top (two-column grid for admins; single column for owners). The notifications list is positioned below.

### 3.8 Communication & Messaging

**Broadcast Announcements (Admin only):**
- Admin selects a building and composes a subject + message body.
- Message is delivered as an in-app notification to all owner-role members of the building.
- Accessible from the Broadcast Announcement panel at the top of the Notification Center page.

**Direct Messaging (All Users):**
- Any user can send a message to building members by selecting:
  - All members of the building
  - Admins only
  - Owners only
  - Specific person(s) (multi-select from building member list)
- Accessible from the Send Message panel at the top of the Notification Center page.
- Messaging restrictions are enforced: users with `messaging_blocked = True` cannot send any messages; users with `individual_messaging_blocked = True` cannot send to "Specific person" recipients.

### 3.9 Audit & Compliance

**Audit Log:**
- Every write operation is logged: entity type, entity ID, action (create, update, delete, activate, deactivate, login, logout, lockout, change_password, assign_user, claim, upload), the performing user, IP address, user agent, and a before/after change delta.
- Admins can view and filter the audit log by: entity type, action text, date range.
- Audit records are append-only — no edits or deletions.

**Data Exports:**
- **Payments CSV:** Date, Unit, Amount, Method, Balance Before, Balance After — filterable by apartment and date range.
- **Expenses CSV / XLSX:** ID, Building, Category, Title, Amount, Date, Split Type — filterable by building and date range. XLSX format generated via openpyxl.

### 3.10 Interactive Tutorial System

A guided in-app walkthrough system that introduces new users to key features. Implemented in React for web and the installable PWA.

**Role-Based Tours:**

- **Admin tour** — 9 steps covering: Dashboard → Create Building → Building Actions → Add Expense → Expense Actions → Manage Users → Expense Categories → Building Assets → Audit Log.
- **Owner tour** — 5 steps covering: Dashboard → Shared Expenses → Payment History → Notifications Centre → Profile.
- The tour role is auto-detected from the authenticated user's role — no manual role selection required.

**Web (React) Implementation:**

- A green "Tour" button in the application header starts the tour immediately based on the user's role.
- The overlay renders via a React portal above all content (z-index 9999+).
- Each step navigates to the target page, then waits for the anchor element to appear in the DOM (up to 2 s via `requestAnimationFrame` retry).
- An SVG mask creates a spotlight cutout over the highlighted element; a blue ring outlines it.
- A floating card shows step badge, title, description, progress dots, and Back / Next / Finish navigation.
- Clicking outside the card closes the tour.
- Anchor IDs are documented in `docs/TUTORIAL_ANCHORS.md` — these DOM `id` attributes must not be removed or renamed without updating the tutorial system.

---

### 3.11 Resident Self-Service & Platform Rules

**Tenant scoping.** Every building is a tenant. Anyone may self-register as an admin, but an admin only sees and changes the buildings they administer (primary admin or co-admin): apartments, expenses, categories, payments, assets, exports, audit log and users. Creating records in a building the admin does not manage is refused with HTTP 403. Residents see only their own building's data.

**Unit claim approval.** A resident who picks their unit in the sign-up wizard sends a request; nothing is assigned until the building's admin approves it (the first approved resident becomes the primary owner, later ones co-owners). Invite links and codes created by an admin skip this step because the admin already authorised them. An admin of the building may still take a unit directly.

**Installable PWA (Android & iOS).** The web app ships a Web App Manifest (Arabic, RTL, standalone) and a service worker that caches the app shell only — never API responses. A banner offers one-tap install on Android; on iPhone it shows the Share → Add to Home Screen steps.

**Shareable invite link.** An admin generates a one-time link `/join/<token>` per unit (email optional) and can share it on WhatsApp. If the invite was created for an email, only the account with that email can redeem it; email-less links go to whoever opens them first. Validation and redemption endpoints are rate-limited; only token links reveal the invited email.

**Building treasury (خزينة العمارة).** The treasury is the building's current balance: starting balance + payments received + asset sales − expenses. It is shown on the admin and resident dashboards (read-only for residents) with the share of units that have paid.

**Pay subscription (InstaPay — display and confirm).** The building admin stores an InstaPay address on the building. A resident taps "دفع الاشتراك", sees the address and amount due, transfers in their banking app, then reports it ("تم الدفع"). The admin confirms or rejects the claim; only confirmation records a payment (method InstaPay) and reduces the balance. No payment gateway is integrated.

**Quick maintenance reports (بلاغ صيانة سريع).** A resident files a report for their building in three taps (elevator, stairs, cleaning, electricity, water, other + optional note). Building admins see reports for buildings they manage and set the status to open, in progress or done.

**Password reset.** A user requests a reset link by email; the link opens a page to choose a new password. The request always answers the same, so registered emails cannot be probed.

**Language and direction.** Arabic and English throughout (backend messages, emails, PDF receipts and web UI) with RTL layout; the app sends the chosen language to the API.

---

## 4. Epics & User Stories

### Epic 1: User Management

**US-1.1: Admin User Management**
As an Admin, I want to create, edit, activate/deactivate, and reset passwords for user accounts, so that access is controlled properly.
- Acceptance: Only Admins can access user management. Deactivated users are refused at login with HTTP 403 (valid credentials, account not allowed).

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

### Epic 10: Interactive Tutorial

**US-10.1: Role-Appropriate Tour**
As a new user, I want to start a guided tour that automatically shows me the features relevant to my role (Admin or Owner) without having to choose manually.

**US-10.2: Step-by-Step Navigation**
As a user, I want the tour to navigate to each relevant page and highlight the key element with a spotlight so I know exactly where to look.

**US-10.3: Dismissible at Any Point**
As a user, I want to be able to exit the tutorial at any step by clicking outside or pressing Finish.

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
Split logic engine handles four split types (equal_all, equal_apartments, equal_stores, custom). Custom split supports optional per-unit weight dictionary; proportional allocation is computed, then each share is rounded up to the nearest 5 via `round_up_to_nearest_5()`. ApartmentExpense records are created (or recalculated on edit) and apartment balances are updated. The recurring-expense job runs daily as a management command using `RecurringConfig.next_due`. Bill attachments uploaded to Cloudinary, metadata stored in `MediaFile` polymorphic table.

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
Database indexes on: building_id, owner_id, expense_id, apartment_id, token (invitations). Pagination on all list endpoints (default page size: 20; clients can request up to 500 via `page_size` query param). Dashboard queries run directly on PostgreSQL (caching is a planned optimization).

**TS-11: Building Asset Management**
`BuildingAsset` and `AssetSale` models. `sell` action on `BuildingAssetViewSet` creates an `AssetSale` record and sets `is_sold=True` (enforced as immutable — no further PATCH allowed after sale). Asset list is scoped by `building_id` query param.

**TS-12: Self-Registration & Invitation System**
`UnitInvitation` model stores token (UUID), `registration_code` (8-char, auto-generated unique), invited_email, expiry, and used_at. `validate` endpoint is public (AllowAny) — returns unit/building info for the wizard UI without requiring auth. `use` endpoint is authenticated — redeems the invite, sets owner on apartment, adds user to building members.

**TS-13: CI/CD & Containerization**
Docker Compose for local development: PostgreSQL 16, Django backend, React frontend (via Vite dev server). GitHub Actions workflows for linting and test automation (planned).

**TS-14: Interactive Tutorial System**
React: Zustand store (`useTutorialStore`) holds `isActive`, `role`, `currentStep`. `TutorialButton` reads `useAuth()` and calls `startTutorial('admin' | 'owner')` directly — no role-picker modal. `waitForElement(anchorId)` uses `requestAnimationFrame` retry (max 2 s) to resolve anchor elements after React Router navigation. SVG mask with `<mask>` element creates a spotlight cutout; a positioned `<Box>` renders the blue highlight ring. `calcCardPos()` tries 6 candidate positions before clamping. All anchor IDs are documented in `docs/TUTORIAL_ANCHORS.md`. Flutter: `WalkthroughController` (ChangeNotifier singleton) with `GlobalKey` anchors; `_SpotlightPainter` uses even-odd `Path` fill; anchor resolution uses `addPostFrameCallback` + 180 ms retry.

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

There is no Celery or Redis in the stack: dashboards query PostgreSQL directly, the one scheduled job is a management command run by the host scheduler, and the cache is in-process.

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
- OpenAPI 3.0 documentation available at `GET /api/schema/` (auto-generated by drf-spectacular).

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
| 0 | Setup & Architecture | Docker Compose, Django project skeleton, React scaffold, PostgreSQL, CI structure | Done |
| 1 | Auth & User Management | JWT login/logout/refresh, RBAC (Admin/Owner), user CRUD, account lockout, profile management, self-registration wizard | Done |
| 2 | Buildings & Apartments | Building CRUD (with co-admins, auto-unit creation), apartment management, unit invitation + registration code flow, unit status | Done |
| 3 | Expense Management | Expense CRUD, 4 split types (including weighted custom), split engine, rounding rule, configurable categories (icon/color/subcategory), 15 default categories, bill upload (Cloudinary), recurring expenses (daily command) | Done |
| 4 | Payment Management | Payment recording (atomic + balance snapshots), payment method tracking, M2M expense linking, carry-forward balance, PDF receipt (ReportLab), balance summary card | Done |
| 5 | Dashboards (Web) | Admin dashboard (income/expense/overdue cards, 12-month bar chart, outstanding balances table), Owner dashboard (balance card, donut chart, recent payments, claim-unit widget) | Done |
| 6 | Notifications & Messaging | In-app notification center (header badge, mark-as-read), expense + payment auto-notifications, broadcast announcements, direct messaging with recipient type selector, messaging restriction enforcement | Done |
| 7 | Building Asset Management | BuildingAsset + AssetSale models, asset CRUD, record-sale action, asset status, summary cards | Done |
| 8 | Audit, Exports & Security | Audit log (all write operations), audit filter UI, CSV/XLSX data exports, account lockout hardening, token blacklist on logout | Done |
| 9 | UX Polish & Bug Fixes | Form label alignment (shrink=true), PDF receipt popup-blocker fix, pagination fix (page_size param), multi-select expenses in record-payment, users scoping to admin's buildings | Done |
| 10 | Testing & QA | Unit tests (pytest), integration tests, E2E tests, load testing | Pending |
| 11 | Deployment & Launch | Production deploy, domain/TLS, monitoring (Sentry), backup configuration | Pending |
| 12 | Mobile Experience (PWA) | Installable Android & iOS experience from the React web app using same backend APIs | Planned |

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
| 17 | Recurring expenses (monthly/quarterly/annual) | ✅ Implemented | Daily management command |
| 18 | Expense detail view with per-unit breakdown + shares total | ✅ Implemented | |
| 19 | Payment recording (atomic, balance snapshots) | ✅ Implemented | select_for_update |
| 20 | Payment method tracking (Cash/BankTransfer/Cheque/Other) | ✅ Implemented | |
| 21 | Link payment to specific expenses (M2M) | ✅ Implemented | |
| 22 | Payment immutability (no edit/delete) | ✅ Implemented | |
| 23 | PDF payment receipt (ReportLab, B5, name-only recorder, owner name) | ✅ Implemented | |
| 24 | Running balance per unit (carry-forward credit) | ✅ Implemented | |
| 25 | Admin dashboard (income, expenses, overdue, chart) | ✅ Implemented | |
| 26 | Owner dashboard (balance card, pie chart, recent payments) | ✅ Implemented | |
| 27 | In-app notification center with unread badge (redesigned: compose top, list below, accordion) | ✅ Implemented | |
| 28 | Broadcast announcement to building owners | ✅ Implemented | |
| 29 | Direct messaging between users with recipient type selector | ✅ Implemented | |
| 30 | Building asset management (track + record sale) | ✅ Implemented | |
| 31 | Full audit log (all write operations) | ✅ Implemented | |
| 32 | CSV/XLSX data exports (payments + expenses) | ✅ Implemented | openpyxl for XLSX |
| 33 | OpenAPI 3.0 documentation (drf-spectacular) | ✅ Implemented | `/api/schema/` |
| 34 | Admin dashboard export/print report | ✅ Implemented | Browser print API |
| 35 | Claim unit by registration code from owner dashboard | ✅ Implemented | |
| 36 | Expense approval workflow | 🔲 Planned | Phase 2, R-7 (approvals & votes) |
| 37 | Bulk expense import via CSV | ✅ Implemented | Phase 3, R-13 |
| 38 | Payment due date reminders (in-app + email + WhatsApp link) | ✅ Implemented | Phase 1, R-1; needs the daily scheduler (DEPLOYMENT section 12) |
| 39 | Multi-currency support | ❌ Descoped | EGP only |
| 40 | Redis caching for dashboard aggregations | 🔲 Pending | Not implemented; no Redis in the stack |
| 41 | Notification preferences UI | ✅ Implemented | Phase 3, R-13 |
| 42 | Unit tests & integration test suite | 🔲 Pending | Sprint 10 |
| 43 | Production deployment + monitoring | 🔲 Pending | Sprint 11 |
| 44 | Installable PWA for Android & iOS (manifest, service worker, install banner) | ✅ Implemented | Replaces the dropped Flutter app; store listing is R-19 |
| 45 | Building photo upload | ✅ Implemented | On the building form |
| 46 | Bulk apartment import via CSV | ✅ Implemented | Phase 3, R-13 |
| 47 | Interactive guided tutorial (Admin 9-step + Owner 5-step tours, auto-role) | ✅ Implemented | React (web and PWA); anchor IDs in TUTORIAL_ANCHORS.md |
| 48 | Multiple owners per unit with shared payment/dashboard visibility | ✅ Implemented | M2M owners; Q-filter on all owner queries |

---

## 11. Roadmap: Business Gaps & Phases

This section records what the product still lacks to run as a business for owners' associations (اتحاد الملاك) in Egypt and the Arab world, grouped into delivery phases. Each requirement has an id (R-n), acceptance criteria, and a status. Statuses: ✅ Implemented · 🟡 In progress · 🔲 Planned · ⏸ Deferred.

### 11.1 Phase overview

| Phase | Goal | Requirements | Exit criteria |
|---|---|---|---|
| **1 — Collect & Show** | Residents pay on time; the building can see and share where the money is | R-1 Payment reminders, R-2 Monthly statement, R-3 Legal pages & account deletion | An admin never has to chase payers by hand; a monthly statement can be shared in the building's WhatsApp group; the app can be launched publicly |
| **2 — People & Governance** | Model who actually lives and decides in a building | R-4 Tenant role, R-5 Board roles, R-6 Admin handover, R-7 Approvals & votes, R-8 Meeting minutes | Tenants can pay; large spending needs approval; a new treasurer takes over without losing history |
| **3 — Plans & Operations** | Predictable income and organised upkeep | R-9 Monthly subscription plan, R-10 Per-unit rates & late fees, R-11 Contractors & obligations calendar, R-12 Maintenance to work order to expense, R-13 Carry-over items | Each unit is billed automatically each month; recurring obligations are tracked and reminded |
| **4 — Business & Scale** | Make 3maracom itself a sustainable product | R-14 Plans & pricing, R-15 Platform billing, R-16 Payment gateway, R-17 Product analytics, R-18 Support channel, R-19 Store distribution, R-20 Annual report | Outside buildings can sign up, pay for 3maracom and be supported |
| **5 — Hardening & Trust** | Make the money trustworthy and auditable | R-21 to R-33 (tenant-safe writes, payment reversals and numbered receipts, expense immutability, owner handover, full audit, approvals, notifications, Arabic completeness, full export) | An admin can correct any money mistake without rewriting history; no action can cross buildings; every money change is audited |

Phases are delivered in order; within a phase, requirements are independent unless a dependency is listed.

### 11.2 Phase 1 — Collect & Show

**R-1 Automatic payment reminders** — ✅ Implemented (command `send_payment_reminders`; WhatsApp action on the admin's unpaid-units table). *Why:* chasing late payers is the admin's biggest chore.
- A daily management command (`send_payment_reminders`, run by the host scheduler) finds each unit's unpaid share of every expense that has a due date.
- Reminders are sent 3 days before the due date, and when overdue: on the first day, then at most once every 7 days. A unit is never reminded twice for the same share on the same day (reminder log).
- Recipients are the unit's owners. Channels: in-app notification and email. Reminder text is bilingual (Arabic first) and states the building, unit, amount still owed and due date.
- Shares already paid (including by manual mark-as-paid) are never reminded.
- The admin's unpaid-units table has a "Remind on WhatsApp" action that opens a pre-filled message to the owner's phone (no WhatsApp Business API required).
- Out of scope in Phase 1: sending via the WhatsApp Business API, SMS.

**R-2 Monthly statement (كشف حساب شهري)** — ✅ Implemented (`GET /buildings/{id}/statement/`, screen `/statement`, bilingual PDF). *Why:* transparency is the brand promise and the statement is what residents forward.
- `GET /buildings/{id}/statement/?month=YYYY-MM` returns the opening balance, payments received (per unit), expenses (with category and date), closing balance, and which units have paid for the month.
- The same data is downloadable as a one-page bilingual PDF (`format=pdf`).
- Visible to the building's admins and residents (read-only); never to other buildings.
- The web app has a statement screen with a month picker, a PDF download and a Share action (system share sheet where supported, download otherwise).
- Opening balance + received − expenses = closing balance, using the same rules as the treasury (starting balance + payments + asset sales − expenses).

**R-3 Legal pages & account deletion** — ✅ Implemented (draft policy text; lawyer review and a support email are still needed before launch). *Why:* required before a public or store launch and for user trust.
- Privacy Policy and Terms of Service pages in Arabic and English, reachable without signing in and linked from the footer and the sign-up form.
- Sign-up requires accepting the terms (checkbox); acceptance time is stored.
- A signed-in user can delete their account (password confirmation). Deletion deactivates the account and removes personal data (name, email, phone, picture) while keeping financial records (payments, expense shares, audit log) attached to an anonymised user.
- The sole administrator of a building cannot delete their account until another administrator takes over (see R-6).
- *Note:* the policy text is a draft for legal review before launch; local legal requirements for handling residents' data must be confirmed.

### 11.3 Phase 2 — People & Governance

**R-4 Tenant (مستأجر) role** — ✅ Implemented as role `renter` (in code, "tenant" already means a building). Owners invite and remove renters from their home screen; building admins do the same from the unit list on the Buildings screen. Tenants live in a unit but do not own it; they often pay the subscription.
- New role `tenant` linked to a unit by the owner or the admin. A tenant sees the unit's dues and the building's treasury and statement, can report maintenance and use "Pay subscription", and cannot see other units' balances or change data.
- The owner remains responsible for the unit; owners see that a tenant is linked and can end the link.
- Invite links can create either an owner or a tenant link.

**R-5 Board roles** — ✅ Implemented (`/board` screen, `GET/POST /buildings/{id}/board/`). One holder per title. The treasurer reviews InstaPay transfers for their building (they see and confirm them from their home screen); the chair approves large expenses (R-7) and the secretary keeps the minutes (R-8). Building admins keep full powers. Roles inside a building: chair (رئيس), treasurer (أمين الصندوق), secretary (أمين السر). Treasurer can record payments and expenses; secretary can send announcements and edit minutes; chair can approve spending. Co-admins keep full powers until roles are assigned.

**R-6 Admin handover** — ✅ Implemented (`POST /buildings/{id}/transfer-admin/` to a co-admin; "Hand over" action on the Buildings screen). The primary administrator can transfer the building to another member; the previous admin becomes co-admin or a resident. All history (payments, audit log) stays intact and the transfer itself is audited. Required by R-3 for admins who want to delete their account.

**R-7 Approvals & votes** — ✅ Implemented. Polls: one vote per unit, owners only, quorum and majority rules, results after closing (`/polls`). Expense approval: a building's `approval_threshold`; a cost above it is created as pending, bills no one and is not counted as spent until the chair approves it, or a resident vote (opened from the expense) approves it; a building with no chair yet is decided by its admins; raising an approved cost above the threshold sends it back to pending. A tie or too few votes leaves it pending. Daily command `finalize_polls` settles votes whose time is up. (Replaces descoped item 36.)
- A building sets an approval threshold. An expense above it is created as "pending approval" and does not bill units until approved by the chair or by a resident vote.
- Polls: an admin creates a question with options and a closing date; each unit gets one vote (co-owners share it); results are visible after closing, with quorum and majority rules set per poll.
- Decisions are recorded with date and result in the audit log and can be attached to minutes.

**R-8 Meeting minutes & documents** — ✅ Implemented (`/records` screen; `/governance/meetings/` with a bilingual PDF, `/governance/documents/` for PDF/JPEG/PNG up to the upload limit). The secretary and building admins write; members read. Files are stored like expense bills (public but unguessable URLs). The secretary records meeting minutes (date, attendees, decisions) and uploads documents (contracts, receipts of work, bylaws). Residents can read; only board roles can edit. Minutes are exportable as PDF.

### 11.4 Phase 3 — Plans & Operations

**R-9 Fixed monthly subscription per unit** — ✅ Implemented (`/subscription` admin screen, `POST /buildings/{id}/subscription/`, daily command `bill_subscriptions`). Charges are stored as expenses of kind `subscription`, which reminders and payment allocation already understand but which are not counted as building costs in the treasury, statement or dashboard. Per-unit coefficients are R-10. *Why:* buildings collect a regular monthly amount (الاشتراك الشهري).
- An admin defines a subscription amount for the building and a billing day. Each month the system bills every unit automatically (daily command), creating a due item that reminders (R-1) and statements (R-2) already understand.
- Amounts can differ by unit type (apartment, store) or by a unit coefficient (R-10).
- Pausing a unit (vacant) is possible with a reason and is audited.

**R-10 Per-unit rates & late fees** — ✅ Implemented (`rate_factor` per unit, edited on the Monthly subscription screen; late fee fixed or percent with grace days; daily command `apply_late_fees`; waive with a recorded reason via `POST /expenses/late-fees/{id}/waive/`). A share is fined at most once; fees are charges, not building costs. Optional per-unit coefficient (e.g. shops pay 1.5×, large flats 1.2×). Optional late fee (fixed amount or percentage) after a grace period; fees are added as separate, visible lines and can be waived by an admin with a recorded reason.

**R-11 Contractors & obligations calendar** — ✅ Implemented (`/operations` screen; `/operations/contractors/` and `/operations/obligations/`). Admins and any board member keep it; members read it. A repeating obligation moves to its next date when marked done (missed periods are skipped); admins and the board are reminded from `remind_days` before the due date and weekly while overdue, and 30 days before a contract ends (daily command `send_obligation_reminders`). A directory of contractors per building (name, trade, phone, contract dates, notes) and a calendar of recurring obligations (elevator maintenance contract renewal, fire-extinguisher inspection, tank cleaning). Obligations remind the board before their due date (same reminder mechanism as R-1).

**R-12 Maintenance report to work order to expense** — ✅ Implemented (`/maintenance/work-orders/`, dialog on the Maintenance screen). Admins and board members assign a contractor and date, follow the status, and link the expense that recorded the cost; the report follows the order and the resident who reported it is told when it is done. The status, contractor, dates and cost show on the report to everyone who can see it. An admin can turn a maintenance report into a work order assigned to a contractor, and link the resulting expense to it. The report shows status, cost and completion date to the reporting resident.

**R-13 Carry-over items** — ✅ Implemented. Notification preferences: a Notifications card on the profile (payment reminders, new expenses, announcements and votes, email). Building photo upload: already on the building form (the earlier "UI not built" note was out of date). Bulk unit import (`POST /buildings/{id}/import-units/`) and bulk expense import (`POST /expenses/import/`): CSV, UTF-8 or Excel-style, checked first then imported all-or-nothing, with every problem row listed. Notification preferences UI (status item 41), building photo upload UI (45), bulk apartment import via CSV (46), bulk expense import (37).

### 11.5 Phase 4 — Business & Scale

**R-14 Plans & pricing** — ✅ Done. Plans are data (`Plan`), edited by platform owners on the Platform page or Django admin: names, monthly/yearly price, unit limit (empty = unlimited) and features (`subscriptions`, `annual_report`). Seeded: Free (10 units), Standard 99/990 EGP (40 units, subscriptions), Plus 249/2490 EGP (unlimited, adds annual report). Each building has its own plan; new buildings get a trial of the top plan (`PlatformSettings.trial_days`, default 14); a lapsed paid plan falls back to Free. Limits are enforced on creating units (single and CSV) and on the gated features; nothing existing is deleted when a limit is passed. Admin page: "Plan". After a paid plan or trial ends, monthly billing and late fees keep running for `PlatformSettings.grace_days` (default 7) and then stop; building admins are reminded at 7, 3, 1 and 0 days before the end and when billing stops (`send_plan_reminders`, run daily).

**R-15 Platform billing** — ✅ Done (manual). A building admin picks a plan and period, sends the amount to the platform InstaPay address (`PlatformSettings.instapay_address`) and reports the reference (`PlanPayment`, price frozen at request). A platform owner confirms or rejects it on the Platform page; confirming sets the plan and extends `paid_until` by one period (from the old end date while still running). Invoices and gateway charging stay with R-16.

**R-16 Payment gateway integration** — ⏸ Deferred until demand is proven. Replace InstaPay "display and confirm" with an integrated flow (card, wallet or InstaPay through a licensed aggregator), automatic reconciliation of payments, and receipts without manual admin confirmation. Needs a provider decision and, likely, legal and fee review.

**R-17 Product analytics & platform KPIs** — ✅ Done (`GET /analytics/platform/`, superusers only, derived from existing data; "Platform" page). Privacy-respecting usage events (sign-ups, activation, payments recorded, reminders sent, monthly active buildings) and an internal dashboard so the business can see which buildings are healthy.

**R-18 Support channel** — ✅ Done (Help page with Arabic FAQ, email/WhatsApp buttons, problem report with screenshot stored as `SupportTicket`, read in Django admin and emailed to `SUPPORT_EMAIL`; set `BRAND.supportWhatsapp` to show the WhatsApp button). An in-app help entry (WhatsApp or email), an FAQ in Arabic, and a way to attach a screenshot to a problem report.

**R-19 Store distribution** — 🔲 Planned. Optional Google Play listing by wrapping the PWA (Trusted Web Activity) once a production domain exists; iOS requires a native wrapper and Apple review and is a separate decision.

**R-20 Annual report** — ✅ Done (`GET /buildings/{id}/annual-report/?year=2026&file_format=pdf`; "Annual" tab on the statement page). A yearly summary for the general assembly: collections by month, expenses by category, balance sheet and unpaid dues, as PDF.

### 11.6 Phase 5 — Hardening & Trust

Source: the business-gap review of 2026-10-30 (SRS audit plus code review). Order of delivery is top to bottom; each item is one commit with tests. Statuses are updated as each lands.

| Id | Requirement | Acceptance criteria | Status |
|---|---|---|---|
| **R-21** | Tenant-safe writes | `building_id` (units, expenses, assets) cannot be changed on update; `category_id` and `apartment_id` must belong to a building the caller manages; a PATCH to another building returns 403/400 and changes nothing. | ✅ Done. Update serializers reject a changed `building_id` (units, expenses, assets); expense `category_id` and custom-split units must belong to the expense's building. |
| **R-22** | Payment reversal and numbered receipts | An admin can reverse a payment with a required reason; the reversal is linked to the original, audited, restores the unit balance and counts negatively in treasury; the receipt shows "voided". Receipts get a sequential number per building. | ✅ Done. `POST /payments/{id}/reverse/` adds a linked negative `Payment` row (negative allocations, balance restored, audit `payment.reversed`); `receipt_no` is sequential per building (backfilled); the PDF shows the number and VOIDED. Reversals net out of treasury, dashboard and exports because they are negative rows. |
| **R-23** | Safe asset sale | `sale_price` must be greater than 0 and `sale_date` valid (400 otherwise, never 500); the asset row is locked so a double sale is impossible. | ✅ Done. The sell action validates through `AssetSaleSerializer` (price > 0, valid date, 400 with field errors) and re-reads the asset with `select_for_update` before recording. |
| **R-24** | Expense immutability once paid | An approved expense with payment allocations cannot be deleted, and its amount, split and units cannot be edited; the API says to use a credit note or reversal. Unpaid expenses stay editable. | ✅ Done. `has_payments()` (net allocations > 0, so fully reversed payments unlock it) blocks delete (400) and amount/split/unit edits (400); title and other descriptive edits are allowed and no longer re-run the split. |
| **R-25** | Owner handover and owner assignment | Changing a unit's owner removes the previous owner's building access unless they hold another unit, writes an `owner_changed` audit entry with the balance at handover, and notifies the admin. Owners can only be assigned from users already in the building or by invite. | ✅ Done. Serializer accepts owners only from users already in the building (member, admin, or on a unit there); the previous owner is removed from the unit and from the building unless they hold another unit; `owner_changed` audit entry carries the balance; building admins are notified. |
| **R-26** | Complete audit of money actions | Audit entries exist for claim reject, plan payment confirm and reject, expense approve and reject (own actions), recurring expense generation, subscription billing and late fees. | ✅ Done. Audit entries added: `reject` (payment_claim), `confirm`/`reject` (plan_payment), `approve`/`reject` (expense, replacing the generic `update`), and one summary entry per building per run for `generate_recurring`, `bill_subscriptions` and `apply_late_fees` (user is null for scheduled jobs). |
| **R-27** | One pending plan payment | A building can have only one pending plan payment at a time; confirming extends the plan once. | ✅ Done. Creating a plan payment locks the building row and returns 400 if one is already pending; a payment reviewed once cannot be confirmed again, so the plan extends once. |
| **R-28** | No self-review of claims | A user cannot confirm or reject a payment claim for a unit they own or rent. (A second-approver rule for all payments is not planned.) | ✅ Done. Claim confirm/reject return 403 when the reviewer (admin or treasurer) owns or rents the claim's unit; they can still review other units. |
| **R-29** | Treasury correctness | `units_paid` counts units with no unpaid shares (credit does not count as paid); treasury shows reversals and sales separately. | ✅ Done. `units_paid` counts billed units whose every share is fully allocated (credit no longer counts); treasury adds `total_payments`, `total_reversals`, `total_sales` while `total_received`/`balance` keep their meaning. |
| **R-30** | Reliable notifications | Notification failures are logged, not swallowed; claim confirm and reject notify the resident. | ✅ Done. The silent `except Exception: pass` blocks around payment, expense and approval notifications (and expense media cleanup) now call `logger.exception`. Claim confirm and reject send the resident an in-app notification in their language (en/ar inline, like the other notifications). |
| **R-31** | Safer account deletion | Deletion rejects pending claims of the user, warns when the user has an outstanding balance (requires confirmation), tells the building admin when a board member leaves, and is blocked for the last platform owner. | ✅ Done. delete-account rejects the user's pending claims, returns 409 `{detail, balance, requires_confirmation}` while they owe a unit balance until `confirm_balance: true` is sent, notifies the building admins when a board member leaves, and returns 409 for the last active platform owner. |
| **R-32** | Arabic completeness | Every backend `_()` string has an Arabic translation; hard-coded Arabic or English strings in views move to translations; the receipt PDF uses a bundled font, not Google Fonts. | ✅ Done. 27 missing Arabic strings added to `locale/ar` (plans, support, subscriptions, auth serializers) and `django.mo` rebuilt; the put-to-vote poll title, options and notification use gettext in the recipient's language; the receipt Google Fonts `@import` was removed (the stack falls back to system fonts, no binary added); `tests/test_translation_completeness.py` fails when a literal `_()`/gettext string has no Arabic msgstr. The `_two/_few/_many` keys in `ar/notifications.json` are kept: they are Arabic plural forms i18next needs. The receipt label tables stay as per-language dictionaries (the receipt language is chosen at render time). |
| **R-33** | Full building export | An admin can download one file per building with units, owners, expenses, payments, claims, late fees and audit log. | 🔲 Planned |
| **D-1** | SRS drift cleanup | Status rows 20, 23, 36, 42, heading 1.2.2, roles in 2.2 and 3.1, rate limiting in 8.2, and sections 6 and 7 match the code. | 🔲 Planned |

### 11.7 Deferred and not planned

| Item | Decision |
|---|---|
| Multi-currency | Not planned; EGP only |
| Visitor and parking management | Not planned; outside the core money-and-upkeep scope |
| Redis caching | Not planned; the stack runs without Redis |
| WhatsApp Business API / SMS | Deferred; Phase 1 uses WhatsApp share links |

### 11.8 Cross-cutting rules for every phase

- Every new screen and message is written Arabic-first, with English, and works in RTL and on a phone.
- Every new endpoint is scoped to the caller's buildings (admins) or membership (residents) and has tests for cross-building access.
- Money-moving actions are audited and idempotent.
- Each requirement ships with backend tests and, where it has UI, a build and lint pass.

---

*— End of Document —*
