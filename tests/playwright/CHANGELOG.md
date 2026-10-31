# Changelog

All notable changes to the ABEM Playwright test framework.

## [1.1.0] - 2026-10-31

### Added
- `tests/api/phase5/`: payment reversal (linked negative entry, balance restored, 409 on a second reversal, reason required,
  tenant isolation), data rules (building_id immutable on units/expenses/assets, paid-expense lock, asset sale validation,
  owner must be a building member, one pending plan payment, account deletion 409 with balance), header-menu notification
  endpoints (unread filter, page_size, unread-count, mark-all-read, scoped to the caller), audit-log scope, building XLSX export.
- `tests/ui/phase5/`: language switch (dir flips, saved to profile, persists after reload, Arabic/RTL checks), notification
  popover (tabs, infinite scroll, mark all read, open center), shared DataTable on Buildings/Users/Expenses/Payments
  (column-naming placeholder, search, sort, pagination), payment reversal dialog with Voided/Reversal chips and receipt numbers,
  plan-page yearly discount, building export download.
- `tests/e2e/test_money_path_cycle.py`: expense -> payment -> receipt -> reversal -> balance restored.
- Page objects `DataTablePage`, `HeaderPage`, `PlanPage`, `RecordsPage`; reversal helpers on `PaymentsPage`;
  `fixtures/phase5.py` (reversible_payment, member_owner, member_owner_page, raw_admin_page) loaded by per-folder conftests.
- Markers: `phase5`, `datatable`, `i18n`, `money_path`.

### Changed
- Tests no longer rely on `role=grid` / DataGrid; tables are the shared plain MUI `DataTable`.

## [1.0.0] - 2026-03-18

### Added
- Complete Playwright-based test automation framework
- API tests for all CRUD resources with positive, negative, and boundary cases
- UI tests for all pages with rendering, form validation, and interaction tests
- E2E journey tests covering 7 critical user flows
- Database assertion tests for data integrity invariants
- Production smoke test suite (15 post-deploy checks)
- Page Object Models for all application pages
- Shared fixtures with automatic setup/teardown
- Custom utilities: API client, DB client, data factory, JWT helpers
- File upload and export helpers
- GitHub Actions CI/CD workflows (push + nightly)
- Security tests: RBAC, tenant isolation, injection, OWASP Top 10
- Performance timing tests with Playwright metrics
- Accessibility tests with axe-playwright
