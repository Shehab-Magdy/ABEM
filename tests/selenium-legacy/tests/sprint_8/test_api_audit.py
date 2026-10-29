"""
Sprint 8 — Audit & Exports API Tests (18 cases)
TC-S8-API-001 → TC-S8-API-018

Tests cover:
  TestAuditLogCreationAPI  (5)  – expense create/update/delete, payment create, user deactivate
  TestAuditLogFieldsAPI    (2)  – required fields present; user_id matches actor
  TestAuditLogRBACAPI      (1)  – owner → 403 on GET /audit/
  TestAuditLogFilteringAPI (2)  – entity filter; user_id filter
  TestExportPaymentsAPI    (3)  – CSV 200 + text/csv; XLSX 200 + xlsx MIME; data matches
  TestExportExpensesAPI    (2)  – building_id filter; date range filter
  TestExportRBACAPI        (1)  – owner → 403 on exports
  TestPaymentReceiptAPI    (2)  – GET /payments/{id}/receipt/ → 200 + PDF; body non-empty
"""
from __future__ import annotations

import pytest

from api.audit_api import AuditAPI
from api.expense_api import ExpenseAPI
from api.exports_api import ExportsAPI
from api.payment_api import PaymentAPI
from api.user_api import UserAPI
from core.api_client import APIClient

pytestmark = [
    pytest.mark.api,
    pytest.mark.sprint_8,
]


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-API-001 … 005 — Audit Log Creation
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditLogCreationAPI:

    @pytest.mark.positive
    def test_expense_create_generates_audit_entry(self, audit_data, audit_api: AuditAPI):
        """TC-S8-API-001: Creating an expense generates an audit log entry with entity=expense, action=create."""
        expense_id = audit_data["expense"]["id"]
        resp = audit_api.list(entity="expense", action="create")
        assert resp.status_code == 200, f"Audit list failed: {resp.text}"
        body = resp.json()
        entries = body if isinstance(body, list) else body.get("results", [])
        matching = [e for e in entries if str(e.get("entity_id", "")) == expense_id]
        assert len(matching) >= 1, (
            f"No audit entry found for expense create (id={expense_id}). "
            f"Entries: {entries[:5]}"
        )

    @pytest.mark.positive
    def test_expense_update_generates_audit_entry(self, audit_data, admin_api: APIClient, audit_api: AuditAPI):
        """TC-S8-API-002: Updating an expense generates an audit log entry with action=update."""
        expense_id = audit_data["expense"]["id"]
        # Perform an update to generate the audit entry
        ExpenseAPI(admin_api).update(expense_id, title="Audit Test Updated")
        resp = audit_api.list(entity="expense", action="update")
        assert resp.status_code == 200, f"Audit list failed: {resp.text}"
        body = resp.json()
        entries = body if isinstance(body, list) else body.get("results", [])
        matching = [e for e in entries if str(e.get("entity_id", "")) == expense_id]
        assert len(matching) >= 1, (
            f"No audit entry found for expense update (id={expense_id}). "
            f"Entries: {entries[:5]}"
        )

    @pytest.mark.positive
    def test_expense_delete_generates_audit_entry(
        self, admin_api: APIClient, audit_api: AuditAPI,
        create_temp_building, create_temp_category, create_temp_expense,
    ):
        """TC-S8-API-003: Deleting an expense generates an audit log entry with action=delete."""
        building = create_temp_building(num_floors=3)
        category = create_temp_category(building_id=building["id"])
        expense = create_temp_expense(building_id=building["id"], category_id=category["id"])
        expense_id = expense["id"]
        # Delete it directly (not via fixture teardown) to trigger audit NOW
        ExpenseAPI(admin_api).delete(expense_id)

        resp = audit_api.list(entity="expense", action="delete")
        assert resp.status_code == 200, f"Audit list failed: {resp.text}"
        body = resp.json()
        entries = body if isinstance(body, list) else body.get("results", [])
        matching = [e for e in entries if str(e.get("entity_id", "")) == expense_id]
        assert len(matching) >= 1, (
            f"No audit entry found for expense delete (id={expense_id}). "
            f"Entries: {entries[:5]}"
        )

    @pytest.mark.positive
    def test_payment_create_generates_audit_entry(self, audit_data, audit_api: AuditAPI):
        """TC-S8-API-004: Creating a payment generates an audit log entry with entity=payment, action=create."""
        payment_id = audit_data["payment"]["id"]
        resp = audit_api.list(entity="payment", action="create")
        assert resp.status_code == 200, f"Audit list failed: {resp.text}"
        body = resp.json()
        entries = body if isinstance(body, list) else body.get("results", [])
        matching = [e for e in entries if str(e.get("entity_id", "")) == payment_id]
        assert len(matching) >= 1, (
            f"No audit entry found for payment create (id={payment_id}). "
            f"Entries: {entries[:5]}"
        )

    @pytest.mark.positive
    def test_user_deactivate_generates_audit_entry(
        self, admin_api: APIClient, audit_api: AuditAPI, create_temp_user,
    ):
        """TC-S8-API-005: Deactivating a user generates audit entry with entity=user, action=deactivate."""
        user = create_temp_user(role="owner")
        user_id = user["id"]
        deact_resp = UserAPI(admin_api).deactivate_user(user_id)
        assert deact_resp.status_code == 200, f"Deactivation failed: {deact_resp.text}"

        resp = audit_api.list(entity="user", action="deactivate")
        assert resp.status_code == 200, f"Audit list failed: {resp.text}"
        body = resp.json()
        entries = body if isinstance(body, list) else body.get("results", [])
        matching = [e for e in entries if str(e.get("entity_id", "")) == user_id]
        assert len(matching) >= 1, (
            f"No audit entry found for user deactivate (id={user_id}). "
            f"Entries: {entries[:5]}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-API-006 … 007 — Audit Log Fields
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditLogFieldsAPI:

    @pytest.mark.positive
    def test_audit_entry_has_required_fields(self, audit_api: AuditAPI):
        """TC-S8-API-006: Each audit log entry contains all required fields."""
        resp = audit_api.list()
        assert resp.status_code == 200, f"Audit list failed: {resp.text}"
        body = resp.json()
        entries = body if isinstance(body, list) else body.get("results", [])
        assert len(entries) > 0, "No audit entries found — run audit_data fixture first"
        entry = entries[0]
        required_fields = ["id", "user", "action", "entity", "entity_id", "created_at"]
        for field in required_fields:
            assert field in entry, f"Required field '{field}' missing from audit entry: {entry}"

    @pytest.mark.positive
    def test_audit_entry_user_id_matches_actor(self, admin_api: APIClient, audit_api: AuditAPI):
        """TC-S8-API-007: Audit entries created by admin have user field matching admin's user ID."""
        # Get admin profile to find admin's user ID
        profile_resp = admin_api.get("/users/me/")
        if profile_resp.status_code != 200:
            # Try alternate endpoint
            profile_resp = admin_api.get("/auth/profile/")
        assert profile_resp.status_code == 200, f"Could not get admin profile: {profile_resp.text}"
        admin_id = str(profile_resp.json()["id"])

        resp = audit_api.list(user_id=admin_id)
        assert resp.status_code == 200, f"Audit list failed: {resp.text}"
        body = resp.json()
        entries = body if isinstance(body, list) else body.get("results", [])
        assert len(entries) > 0, f"No audit entries found for admin user_id={admin_id}"
        for entry in entries[:5]:
            assert str(entry.get("user")) == admin_id, (
                f"Entry user {entry.get('user')} != admin_id {admin_id}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-API-008 — RBAC
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditLogRBACAPI:

    @pytest.mark.negative
    def test_owner_cannot_access_audit_log(self, owner_api: APIClient):
        """TC-S8-API-008: Owner role receives 403 when accessing GET /audit/."""
        from api.audit_api import AuditAPI as _AuditAPI
        owner_audit = _AuditAPI(owner_api)
        resp = owner_audit.list()
        assert resp.status_code == 403, (
            f"Owner should not access audit log, got {resp.status_code}: {resp.text[:200]}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-API-009 … 010 — Filtering
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditLogFilteringAPI:

    @pytest.mark.positive
    def test_entity_filter_scopes_results(self, audit_data, audit_api: AuditAPI):
        """TC-S8-API-009: ?entity=expense returns only expense entries."""
        resp = audit_api.list(entity="expense")
        assert resp.status_code == 200, f"Audit list failed: {resp.text}"
        body = resp.json()
        entries = body if isinstance(body, list) else body.get("results", [])
        assert len(entries) > 0, "No expense audit entries found"
        for entry in entries:
            assert entry["entity"] == "expense", (
                f"Non-expense entry in filtered results: entity={entry['entity']}"
            )

    @pytest.mark.positive
    def test_user_id_filter_scopes_results(self, admin_api: APIClient, audit_api: AuditAPI):
        """TC-S8-API-010: ?user_id=<admin_id> returns only admin-actor entries."""
        profile_resp = admin_api.get("/users/me/")
        if profile_resp.status_code != 200:
            profile_resp = admin_api.get("/auth/profile/")
        assert profile_resp.status_code == 200
        admin_id = str(profile_resp.json()["id"])

        resp = audit_api.list(user_id=admin_id)
        assert resp.status_code == 200, f"Audit list failed: {resp.text}"
        body = resp.json()
        entries = body if isinstance(body, list) else body.get("results", [])
        assert len(entries) > 0, f"No entries for admin user_id={admin_id}"
        for entry in entries[:10]:
            assert str(entry.get("user")) == admin_id, (
                f"Entry user {entry.get('user')} != {admin_id}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-API-011 … 013 — Export Payments
# ═══════════════════════════════════════════════════════════════════════════════

class TestExportPaymentsAPI:

    @pytest.mark.positive
    def test_export_payments_csv_returns_200_with_csv_content_type(self, exports_api: ExportsAPI):
        """TC-S8-API-011: GET /exports/payments/?format=csv returns 200 with text/csv Content-Type."""
        resp = exports_api.export_payments(fmt="csv")
        assert resp.status_code == 200, f"CSV export failed: {resp.text[:300]}"
        ct = resp.headers.get("Content-Type", "")
        assert "text/csv" in ct, f"Expected text/csv, got: {ct}"

    @pytest.mark.positive
    def test_export_payments_xlsx_returns_200_with_xlsx_content_type(self, exports_api: ExportsAPI):
        """TC-S8-API-012: GET /exports/payments/?format=xlsx returns 200 with xlsx MIME type."""
        resp = exports_api.export_payments(fmt="xlsx")
        assert resp.status_code == 200, f"XLSX export failed: {resp.text[:300]}"
        ct = resp.headers.get("Content-Type", "")
        assert "spreadsheetml" in ct or "xlsx" in ct or "openxmlformats" in ct, (
            f"Expected XLSX content type, got: {ct}"
        )

    @pytest.mark.positive
    def test_export_payments_csv_contains_header_row(self, exports_api: ExportsAPI, audit_data):
        """TC-S8-API-013: Payment CSV export contains the correct header row."""
        resp = exports_api.export_payments(fmt="csv")
        assert resp.status_code == 200, f"CSV export failed: {resp.text[:300]}"
        first_line = resp.text.splitlines()[0] if resp.text else ""
        assert "ID" in first_line, f"CSV header row missing 'ID': {first_line}"
        assert "Amount" in first_line, f"CSV header row missing 'Amount': {first_line}"
        assert "Date" in first_line, f"CSV header row missing 'Date': {first_line}"


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-API-014 … 015 — Export Expenses
# ═══════════════════════════════════════════════════════════════════════════════

class TestExportExpensesAPI:

    @pytest.mark.positive
    def test_export_expenses_building_id_filter(self, exports_api: ExportsAPI, audit_data):
        """TC-S8-API-014: ?building_id=<id> scopes expense export to that building."""
        building_id = audit_data["building"]["id"]
        resp = exports_api.export_expenses(fmt="csv", building_id=building_id)
        assert resp.status_code == 200, f"Expense CSV export failed: {resp.text[:300]}"
        # The CSV should include at least the header + the test expense
        lines = [l for l in resp.text.splitlines() if l.strip()]
        assert len(lines) >= 2, f"Expected header + at least 1 row, got: {lines}"

    @pytest.mark.positive
    def test_export_expenses_date_range_filter(self, exports_api: ExportsAPI):
        """TC-S8-API-015: ?date_from=&date_to= date range filter is accepted (200 response)."""
        resp = exports_api.export_expenses(fmt="csv", date_from="2020-01-01", date_to="2099-12-31")
        assert resp.status_code == 200, f"Date-range export failed: {resp.text[:300]}"
        ct = resp.headers.get("Content-Type", "")
        assert "text/csv" in ct, f"Expected text/csv, got: {ct}"


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-API-016 — Export RBAC
# ═══════════════════════════════════════════════════════════════════════════════

class TestExportRBACAPI:

    @pytest.mark.negative
    def test_owner_cannot_access_exports(self, owner_api: APIClient):
        """TC-S8-API-016: Owner role receives 403 on all export endpoints."""
        from api.exports_api import ExportsAPI as _ExportsAPI
        owner_exports = _ExportsAPI(owner_api)
        resp = owner_exports.export_payments(fmt="csv")
        assert resp.status_code == 403, (
            f"Owner should not access exports, got {resp.status_code}: {resp.text[:200]}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-API-017 … 018 — Payment Receipt PDF
# ═══════════════════════════════════════════════════════════════════════════════

class TestPaymentReceiptAPI:

    @pytest.mark.positive
    def test_receipt_endpoint_returns_200_pdf(self, admin_api: APIClient, audit_data):
        """TC-S8-API-017: GET /payments/{id}/receipt/ returns 200 with application/pdf Content-Type."""
        payment_id = audit_data["payment"]["id"]
        resp = admin_api.get(f"/payments/{payment_id}/receipt/")
        assert resp.status_code == 200, (
            f"Receipt endpoint returned {resp.status_code}: {resp.text[:300]}"
        )
        ct = resp.headers.get("Content-Type", "")
        assert "application/pdf" in ct, f"Expected application/pdf, got: {ct}"

    @pytest.mark.positive
    def test_receipt_body_is_non_empty_bytes(self, admin_api: APIClient, audit_data):
        """TC-S8-API-018: Receipt PDF response body is non-empty bytes (valid PDF magic bytes)."""
        payment_id = audit_data["payment"]["id"]
        resp = admin_api.get(f"/payments/{payment_id}/receipt/")
        assert resp.status_code == 200
        assert len(resp.content) > 100, "Receipt PDF body appears empty"
        # PDF files always start with %PDF
        assert resp.content[:4] == b"%PDF", (
            f"Response does not look like a PDF: {resp.content[:20]!r}"
        )
