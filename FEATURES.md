# ABEM — Feature Inventory

**Apartment & Building Expense Management**
Last updated: 2026-03-23 · Covers: Web Frontend, REST API, Django Backend

---

## 1. Authentication & User Management

| Feature | Description |
|---------|-------------|
| **JWT Authentication** | Access tokens (15 min) and refresh tokens (7 days) via `djangorestframework-simplejwt`. Role and tenant IDs embedded in token claims. |
| **Role-Based Access Control** | Two roles — **Admin** (full CRUD on buildings, expenses, users) and **Owner** (read-only view of own apartment data). Route guards enforce role at both API and frontend levels. |
| **Self-Registration Wizard** | Three paths: Admin sign-up (creates building), Owner sign-up (claims unit), and Invite-code redemption. Language selection persisted to DB at account creation. |
| **Admin User Creation** | Admins create users via `/api/v1/users/` with role assignment, building assignment (for admins), and unit assignment (for owners). Users scoped to creating admin's buildings. |
| **Account Lockout** | Configurable failed-login threshold (default 5 attempts, 30-minute lockout). Tracks `failed_login_attempts` and `locked_until`. |
| **Forced Password Change** | After an admin resets a user's password, `must_change_password` flag redirects the user to a password change screen on next login. |
| **Password Reset** | Admin-initiated reset generates a temporary password and sets the forced-change flag. |
| **Profile Management** | Users update display name, phone, profile picture (Cloudinary upload), and preferred language. Language preference syncs across devices via `usePreferredLanguage` hook. |
| **User Deactivation** | Soft-disable accounts — blocks login without deleting payment or expense history. Reversible via reactivation. |
| **Messaging Restrictions** | Admins can block a user from sending broadcast or individual messages. |
| **Session Expiry Warning** | 30 seconds before token expiry, checks idle time. If idle ≥ 60s → shows countdown modal. If active → silently refreshes token in background. Auto-logout at countdown zero. |
| **Created-By Tracking** | `created_by` FK on User model scopes the admin users list to users the current admin created or manages. |

---

## 2. Buildings

| Feature | Description |
|---------|-------------|
| **Building CRUD** | Create, read, update, soft-delete buildings with address, city, country, floors, apartment/store counts, and photo. |
| **Multi-Admin Support** | Primary admin FK plus co-admin M2M (`BuildingCoAdmin`). Co-admins have the same management privileges. |
| **Building Activation** | Toggle `is_active` flag to temporarily disable a building without deleting it. |
| **Member Management** | `UserBuilding` junction table tracks which users belong to which buildings. Auto-joined on unit claim or invite redemption. |
| **Building Directory** | Public-facing endpoint lists active buildings for the self-registration wizard. |

---

## 3. Apartments & Units

| Feature | Description |
|---------|-------------|
| **Unit CRUD** | Create and manage units within buildings. Each unit has a number, floor, size (sqm), type, and status. |
| **Unit Types** | Apartment or Store — affects expense split calculations. |
| **Unit Statuses** | Occupied, Vacant, Under Maintenance — translated in both English and Arabic. |
| **Owner Assignment** | Primary owner FK plus co-owners M2M. Admin assigns owners through the user form or the Manage Units dialog. |
| **Running Balance** | Decimal balance field on each apartment. Positive = owes money, negative = credit. Updated atomically on expense splits and payments. |
| **Invite System** | Admin generates a one-time invite link with UUID token + 8-character registration code. Owner redeems to claim the unit. 30-day expiry. |
| **Available Units** | Endpoint returns unowned units in a building for the registration wizard's unit picker. |

---

## 4. Expenses

| Feature | Description |
|---------|-------------|
| **Expense Records** | Title, description, amount, expense date, due date, category, split type, bill attachment. Soft-delete with `deleted_at` timestamp. |
| **Split Engine** | Distributes expense amount across units. Four modes: Equal All, Equal Apartments Only, Equal Stores Only, Custom Weighted. Shares rounded up to nearest 5 EGP. |
| **Recurring Expenses** | Optional recurring config with frequency (Monthly, Quarterly, Annual) and `next_due` date. Celery Beat schedules auto-generation. |
| **Expense Categories** | Per-building hierarchical categories with parent/subcategory support, Material icon, and hex color. 15 seeded defaults, all translated. Subcategories rendered nested with indent in UI. |
| **Mark as Paid** | Admin toggle (`is_manually_paid`) overrides computed status to "Paid" building-wide, regardless of individual balances. Logged as `expense.marked_paid`. |
| **Bill Upload** | File upload (JPEG, PNG, PDF, max 10 MB) stored in Cloudinary. Linked to expense via polymorphic MediaFile model. |
| **Auto-Computed Status** | Per-owner and per-unit payment status derived from actual payments vs share amounts. No redundant boolean — computed at serialization time. |
| **Owner Notifications** | Apartment owners auto-notified when a new expense is added to their building. |

---

## 5. Payments

| Feature | Description |
|---------|-------------|
| **Immutable Ledger** | Payments are create-only (no update or delete). Balance snapshots (`balance_before`, `balance_after`) recorded atomically with `SELECT FOR UPDATE`. |
| **Payment Methods** | Cash, Bank Transfer, Cheque, Mobile Wallet, Other — all translated in both languages. |
| **Expense Allocation** | When linking a payment to multiple expenses, admin can specify per-expense `allocated_amount`. Running total with validation (sum ≤ amount paid). Unallocated remainder carries forward as credit. |
| **PDF Receipt** | WeasyPrint HTML→PDF receipt with bilingual support. Arabic mode: RTL layout, Noto Sans Arabic font, Eastern Arabic numerals (٠-٩), labels on right / values on left. A6 paper size. |
| **Balance Management** | Apartment balance decremented atomically on payment. Positive = owes, negative = credit. |

---

## 6. Building Assets

| Feature | Description |
|---------|-------------|
| **Asset Register** | Track physical equipment per building — elevators, generators, pumps, CCTV, etc. Fields: name, type (Vehicle, Equipment, Furniture, Electronics, Property, Other), acquisition date, acquisition value. |
| **Asset Sales** | Record disposal with buyer details, sale price, sale date, and notes. One-to-one relationship to asset. |

---

## 7. Notifications

| Feature | Description |
|---------|-------------|
| **Notification Types** | Payment Due, Payment Overdue, Payment Confirmed, Expense Added, Expense Updated, User Registered, Announcement, Message. |
| **In-App Notifications** | User-scoped list with read/unread filter. Mark individual as read. Unread badge in header sidebar updates instantly via Zustand store. |
| **Broadcast Announcements** | Admin sends to all building members (admins + owners). Grouped under `broadcast_group` UUID for read-by tracking. |
| **Read-By Analytics** | Admin sees "Read by X/Y" on announcements. Hover tooltip shows reader names with profile avatars. Lazy-loaded on hover, cached per notification. |
| **Direct Messaging** | Send messages to all members, admins only, owners only, or specific individuals. Message type shows distinct chip label. |
| **Bilingual Content** | Notification body generated in recipient's preferred language via `NOTIFICATION_CONTENT` template dict with token substitution. |

---

## 8. Dashboard & Analytics

| Feature | Description |
|---------|-------------|
| **Admin Dashboard** | Total income, total expenses, overdue unit count, building count. Month-over-month trend percentages. Monthly bar chart. Building selector and date range filters. Unpaid units table with sortable columns. Payment coverage progress bar. SVG header banner (RTL-mirrored in Arabic). |
| **Owner Dashboard** | Personal balance summary, recent payments list, recent expenses list. Scoped to owned units only. Pie chart breakdown. Currency values formatted with `Intl.NumberFormat` (EGP / ج.م). |

---

## 9. Audit Log

| Feature | Description |
|---------|-------------|
| **Immutable Append-Only Log** | Every write operation calls `log_action()` recording: acting user, action label, entity type, entity ID, before/after change diff (JSON), IP address, and user agent. |
| **Actions Tracked** | create, update, delete, login, logout, lockout, activate, deactivate, reset_password, expense.marked_paid, payment.distributed, user.buildings_assigned, and more. |
| **Admin Viewer** | Filterable by entity, user, action, and date range. Accessible from direct URL only (removed from footer and tour). |

---

## 10. Data Exports

| Feature | Description |
|---------|-------------|
| **Payment Export** | CSV download filtered by apartment and date range. Columns: ID, Apartment, Amount, Method, Date, Balance Before/After. |
| **Expense Export** | CSV download filtered by building and date range. Columns: ID, Building, Category, Title, Amount, Date, Split Type. |

---

## 11. Internationalization & RTL

| Feature | Description |
|---------|-------------|
| **Dual Language** | English and Arabic with 14 translation namespaces (common, auth, dashboard, buildings, expenses, payments, notifications, users, categories, profile, errors, audit, exports, tutorial). |
| **RTL Layout** | MUI dual-theme approach — `ltrTheme` (Inter font) and `rtlTheme` (Cairo font) with `stylis-plugin-rtl`. Emotion CSS cache recreated on direction switch. |
| **Eastern Arabic Numerals** | Financial values display with `Intl.NumberFormat("ar-EG")`. Input fields accept ٠-٩ via dual-layer hook (beforeinput + focusout) and Axios interceptor safety net. Phone fields also normalize Arabic digits. |
| **Translation Completeness** | CI script (`scripts/check_translations.js`) validates en/ar key parity with Arabic plural suffix awareness (`_two`, `_few`, `_many`). |
| **Backend i18n** | `APILanguageMiddleware` activates language from `Accept-Language` header. Validation errors and choice labels returned in requested language. Django Rosetta admin interface for translation management. |

---

## 12. Interactive Tutorial

| Feature | Description |
|---------|-------------|
| **Guided Tour** | SVG spotlight overlay with floating tooltip card. Role-based: Admin tour (9 steps) covers dashboard → buildings → expenses → users → categories → assets → profile. Owner tour (5 steps) covers dashboard → expenses → payments → notifications → profile. |
| **RTL-Aware Positioning** | Card position candidates reordered for RTL. Inline `style` used for coordinates to bypass stylis-plugin-rtl flipping. |
| **Progress Tracking** | Dot indicators, step counter (e.g., "3 of 9"), Previous/Next/Finish navigation. |

---

## 13. Performance

| Feature | Description |
|---------|-------------|
| **Lazy Loading** | All 16 route-level components loaded via `React.lazy` + `Suspense` for code-split bundles. |
| **Request Cancellation** | `AbortController` infrastructure in Axios client. Applied in buildings and payments pages to cancel in-flight requests on unmount. |
| **Query Optimization** | `select_related` and `prefetch_related` on expenses (category, apartment_expenses), buildings (co_admins), payments (apartment, recorded_by), and notifications (sender) querysets. |
| **Database Indexes** | Targeted indexes on email, role, is_read, (user + is_read), (entity + entity_id), payment_date, expense_date, broadcast_group. |
| **Pagination** | Default 20 items, max 100. Requests exceeding 100 return 400. |
| **GZip Compression** | `GZipMiddleware` compresses API responses. |
| **Static Caching** | WhiteNoise serves static files with 1-year immutable cache headers for hashed assets. |

---

## 14. Infrastructure

| Component | Details |
|-----------|---------|
| **PostgreSQL 16** | Primary database with persistent volume. Health-checked via `pg_isready`. |
| **Redis 7** | Celery broker and result backend. Health-checked via `redis-cli ping`. |
| **Django 4.2** | Backend API server with DRF, SimpleJWT, drf-spectacular (OpenAPI docs at `/api/docs/`). |
| **Celery Worker** | Async task processing for notifications and exports. |
| **Celery Beat** | Scheduler for recurring expense generation and payment reminders. |
| **Vite Dev Server** | React 18 frontend with HMR on port 5173. |
| **Docker Compose** | Full development stack in one command. `restart.sh` for service restart with health checks and optional smoke tests. `test.sh` for running Playwright tests. |
| **Playwright Test Suite** | 300+ tests across smoke, API, UI, E2E, and DB layers. Headless Chromium with HTML report generation. |
| **ESLint v9** | Flat config (`eslint.config.js`) with React and React Hooks plugins. |
| **CI/CD** | GitHub Actions: lint, translation check, build verification. |
