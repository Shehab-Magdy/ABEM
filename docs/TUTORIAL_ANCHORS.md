# TUTORIAL_ANCHORS.md
## 3maracom Interactive Tutorial — Anchor Reference

> **DO NOT remove or rename these DOM ids without updating
> `TutorialOverlay.jsx` (React; also used by the mobile PWA).**
> They are load-bearing for the interactive tutorial system.

---

## React (Web) — DOM `id` attributes

| `id` | File | Element type | Tutorial step |
|------|------|--------------|---------------|
| `language-switch` | `components/LanguageToggleButton.jsx` | Button (header) | Admin step 2 / Owner step 2 — Switch language |
| `notification-bell` | `components/NotificationMenu.jsx` | IconButton (header) | Admin step 3 / Owner step 3 — Notifications bell. On phones (< 600px) only the bell is highlighted |
| `notification-menu-panel` | `components/NotificationMenu.jsx` | Popover paper | Same step on >= 600px: the tour opens the popover (clicks the bell) and closes it on leaving the step (Escape) |
| `add-building-btn` | `pages/buildings/BuildingsPage.jsx` | Button | Admin step 4 — Create your first building |
| `building-actions-row` | `pages/buildings/BuildingsPage.jsx` | Stack (DataTable actions cell of the first row) | Admin step 5 — Building actions |
| `add-expense-btn` | `pages/expenses/ExpensesPage.jsx` | Button | Admin step 6 — Add a shared expense |
| `expenses-table` | `pages/expenses/ExpensesPage.jsx` | DataTable container (search, sort, paging) | Admin step 7 — Expense table & actions; Owner step 4 — Your shared expenses |
| `expense-actions-btn` | `pages/expenses/ExpensesPage.jsx` | Stack (per-row action buttons) | — (kept; no longer a step target) |
| `payments-table` | `pages/payments/PaymentsPage.jsx` | DataTable container | Admin step 8 — Payments & receipts (reversal, receipt no); Owner step 5 — Your payment history |
| `export-building-btn` | `pages/records/RecordsPage.jsx` | Button (admin only) | Admin step 9 — Building export |
| `add-user-btn` | `pages/users/UsersPage.jsx` | Button | Admin step 10 — Manage users |
| `categories-table` | `pages/expenses/ExpenseCategoriesPage.jsx` | DataTable container | Admin step 11 — Expense categories |
| `assets-table` | `pages/assets/AssetsPage.jsx` | DataTable container | Admin step 12 — Building assets |
| `audit-table` | `pages/audit/AuditLogPage.jsx` | DataTable container | Admin step 13 — Audit log |
| `plan-period-toggle` | `pages/plans/PlanPage.jsx` | ToggleButtonGroup (Monthly / Yearly) | Admin step 14 — Your plan |
| `notifications-list` | `pages/notifications/NotificationCenterPage.jsx` | Stack of items, or the empty-state Alert when there are none | Owner step 6 — Notification center |
| `profile-card` | `pages/profile/ProfilePage.jsx` | Box (page root) | — |
| `tutorial-profile-form` | `pages/profile/ProfilePage.jsx` | Box (wraps profile form section) | Admin step 16 / Owner step 8 — Your profile |
| `tutorial-btn` | `tutorial/TutorialOverlay.jsx` | Button (in header) | — (meta: starts the tour) |

The overlay follows its anchor if content loads late, brings it into view, highlights only the top part of anchors taller than half the viewport, and wraps its layers in `#tutorial-root` (also load-bearing: it is made reachable while the notification popover is open).

All tables are the shared `components/DataTable.jsx`; its `id` prop lands on the TableContainer.

### Steps with no anchor (centered card)

| Role | Step | Page | Reason |
|------|------|------|--------|
| Admin | 1 | `/dashboard` | Full-page overview; no single element to highlight |
| Admin | 15 | `/help` | "More tools": the side menu (closed on phones) has no stable single anchor |
| Owner | 1 | `/dashboard` | Same as admin step 1 |
| Owner | 7 | `/help` | "More tools", same reason |

---

## Adding new tutorial steps

1. Add a step object to `TUTORIAL_STEPS` in `TutorialOverlay.jsx`.
2. Add a `id="your-anchor-id"` prop to the target element.
3. Add a row to this table.
4. Add `titleKey`/`descKey` strings to BOTH `public/locales/en/tutorial.json` and `ar/tutorial.json` (texts are not kept in the JSX).
5. A step that opens a popover must set a flag like `openBell` and have the overlay close it when the step changes or the tour ends.
