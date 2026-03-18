"""DB tests for audit log completeness."""
import pytest
from utils.data_factory import build_building, build_expense, build_payment
from utils.db_client import get_audit_logs


@pytest.mark.db
class TestAuditLogCompleteness:
    def test_expense_creation_logged(self, admin_api, db_conn, seeded_expense):
        logs = get_audit_logs(db_conn, entity="expense")
        assert len(logs) > 0

    def test_payment_recorded_logged(self, admin_api, db_conn, seeded_payment):
        logs = get_audit_logs(db_conn, entity="payment")
        assert len(logs) > 0

    def test_audit_log_persists_after_entity_delete(self, admin_api, db_conn, seeded_building):
        bid = seeded_building["building"]["id"]
        cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        expense = admin_api.post("/api/v1/expenses/", data=build_expense(bid, cat_list[0]["id"])).json()
        admin_api.delete(f"/api/v1/expenses/{expense['id']}/")
        logs = get_audit_logs(db_conn, entity="expense", entity_id=expense["id"])
        assert len(logs) > 0
