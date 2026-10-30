# TUTORIAL_ANCHORS.md
## 3maracom Interactive Tutorial — Anchor Reference

> **DO NOT remove or rename these DOM ids without updating
> `TutorialOverlay.jsx` (React; also used by the mobile PWA).**
> They are load-bearing for the interactive tutorial system.

---

## React (Web) — DOM `id` attributes

| `id` | File | Element type | Tutorial step |
|------|------|--------------|---------------|
| `add-building-btn` | `pages/buildings/BuildingsPage.jsx` | Button | Admin step 2 — Create your first building |
| `building-actions-row` | `pages/buildings/BuildingsPage.jsx` | Stack (DataGrid renderCell) | Admin step 3 — What you can do with a building |
| `add-expense-btn` | `pages/expenses/ExpensesPage.jsx` | Button | Admin step 4 — Add a shared expense |
| `expense-actions-btn` | `pages/expenses/ExpensesPage.jsx` | Stack (per-row action buttons) | Admin step 5 — Expense actions explained |
| `expenses-table` | `pages/expenses/ExpensesPage.jsx` | TableContainer | Owner step 2 — Your shared expenses |
| `add-user-btn` | `pages/users/UsersPage.jsx` | Button | Admin step 6 — Manage users |
| `categories-table` | `pages/expenses/ExpenseCategoriesPage.jsx` | TableContainer | Admin step 7 — Expense categories |
| `assets-table` | `pages/assets/AssetsPage.jsx` | TableContainer | Admin step 8 — Building assets |
| `payments-table` | `pages/payments/PaymentsPage.jsx` | TableContainer | Owner step 3 — Your payment history |
| `notifications-list` | `pages/notifications/NotificationCenterPage.jsx` | Stack | Owner step 4 — Notifications centre |
| `profile-card` | `pages/profile/ProfilePage.jsx` | Box (page root) | Owner step 5 — Your profile |
| `tutorial-profile-form` | `pages/profile/ProfilePage.jsx` | Box (wraps profile form section) | Admin step 9 — Your Profile; Owner step 5 — Your profile |
| `tutorial-btn` | `tutorial/TutorialOverlay.jsx` | Button (in header) | — (meta: opens role picker) |

### Steps with no anchor (centered card)

| Role | Step | Page | Reason |
|------|------|------|--------|
| Admin | 1 | `/dashboard` | Full-page overview; no single element to highlight |
| Owner | 1 | `/dashboard` | Same |

---

## Adding new tutorial steps

1. Add a step object to `TUTORIAL_STEPS` in `TutorialOverlay.jsx`.
2. Add a `id="your-anchor-id"` prop to the target element.
3. Add a row to this table.
