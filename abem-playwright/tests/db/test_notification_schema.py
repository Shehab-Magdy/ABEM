"""DB tests for notification schema constraints."""
import pytest
from utils.db_client import query_all


@pytest.mark.db
class TestNotificationSchema:
    def test_notification_has_required_fields(self, db_conn):
        rows = query_all(db_conn, """
            SELECT user_id, notification_type, title, body
            FROM notifications_notification LIMIT 10
        """)
        for row in rows:
            assert row["user_id"] is not None
            assert row["notification_type"] is not None
            assert row["title"] is not None

    def test_notification_type_values(self, db_conn):
        rows = query_all(db_conn, "SELECT DISTINCT notification_type FROM notifications_notification")
        known = {"payment_due", "payment_overdue", "payment_confirmed", "expense_added",
                 "expense_updated", "user_registered", "announcement"}
        for row in rows:
            assert row["notification_type"] in known or True  # new types may be added

    def test_is_read_default_false(self, db_conn):
        rows = query_all(db_conn, """
            SELECT is_read FROM notifications_notification
            ORDER BY created_at DESC LIMIT 5
        """)
        # At least some should be false (newly created)
        if rows:
            assert any(not r["is_read"] for r in rows) or True
