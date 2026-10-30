# Changelog

All notable changes to the ABEM Playwright test framework.

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
