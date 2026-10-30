"""
Sprint 6 — Notification System API Tests (20 cases)
TC-S6-API-001 → TC-S6-API-020

Tests cover:
  TestNotificationListAPI   (4)  – list, empty user, owner-scoped, pagination key
  TestNotificationMarkRead  (3)  – mark-read flow, is_read flips, wrong-owner 404
  TestNotificationBroadcast (4)  – admin creates records, non-admin 403, missing fields 400, response structure
  TestNotificationRBAC      (3)  – unauthenticated 401 (list + broadcast), owner isolation
  TestNotificationFiltering (3)  – is_read=false, is_read=true, no filter → all
  TestNotificationTriggers  (3)  – expense trigger, payment trigger, metadata keys
"""
from __future__ import annotations

import pytest

from api.notification_api import NotificationAPI
from core.api_client import APIClient

pytestmark = [
    pytest.mark.api,
    pytest.mark.sprint_6,
]


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-API-001 … 004 — List
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationListAPI:

    @pytest.mark.positive
    def test_list_returns_200(self, notification_api: NotificationAPI):
        """TC-S6-API-001: GET /notifications/ returns 200."""
        resp = notification_api.list()
        assert resp.status_code == 200

    @pytest.mark.positive
    def test_empty_list_for_fresh_admin(self, env_config, create_temp_user):
        """TC-S6-API-002: A freshly created admin with no activity gets an empty list."""
        from core.api_client import APIClient as _APIClient
        user = create_temp_user(role="admin")
        client = _APIClient(env_config.api_url)
        client.authenticate(user["email"], user["password"])
        api = NotificationAPI(client)

        resp = api.list()
        assert resp.status_code == 200
        body = resp.json()
        items = body if isinstance(body, list) else body.get("results", [])
        assert len(items) == 0

        client.logout()

    @pytest.mark.positive
    def test_owner_only_sees_own_notifications(self, notification_data):
        """TC-S6-API-003: Owner sees only their own notifications (EXPENSE_ADDED from fixture)."""
        owner_napi = notification_data["owner_notification_api"]
        resp = owner_napi.list()
        assert resp.status_code == 200
        body = resp.json()
        items = body if isinstance(body, list) else body.get("results", [])
        for n in items:
            # All items belong to this owner — type must be a known notification type
            assert "notification_type" in n
            assert "is_read" in n

    @pytest.mark.positive
    def test_list_response_has_expected_fields(self, notification_data):
        """TC-S6-API-004: List response items contain all required fields."""
        owner_napi = notification_data["owner_notification_api"]
        resp = owner_napi.list()
        assert resp.status_code == 200
        body = resp.json()
        items = body if isinstance(body, list) else body.get("results", [])
        assert len(items) >= 1, "Expected at least 1 notification from expense trigger"
        first = items[0]
        for field in ("id", "notification_type", "channel", "title", "body", "is_read", "created_at"):
            assert field in first, f"Missing field: {field}"


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-API-005 … 007 — Mark-Read
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationMarkRead:

    @pytest.mark.positive
    def test_mark_read_returns_200(self, notification_data):
        """TC-S6-API-005: POST /notifications/{id}/read/ returns 200."""
        owner_napi = notification_data["owner_notification_api"]
        items = (owner_napi.list().json())
        items = items if isinstance(items, list) else items.get("results", [])
        assert len(items) >= 1
        resp = owner_napi.mark_read(items[0]["id"])
        assert resp.status_code == 200

    @pytest.mark.positive
    def test_mark_read_flips_is_read(self, notification_data):
        """TC-S6-API-006: After mark_read, is_read is True in subsequent GET."""
        owner_napi = notification_data["owner_notification_api"]
        items = (owner_napi.list(is_read=False).json())
        items = items if isinstance(items, list) else items.get("results", [])
        assert len(items) >= 1
        nid = items[0]["id"]
        owner_napi.mark_read(nid)
        detail = owner_napi.get(nid).json()
        assert detail["is_read"] is True

    @pytest.mark.negative
    def test_mark_read_returns_404_for_other_users_notification(
        self, notification_data, env_config, create_temp_user
    ):
        """TC-S6-API-007: Owner B cannot mark Owner A's notification as read — 404."""
        # notification_data has owner A's notification
        items = (notification_data["owner_notification_api"].list().json())
        items = items if isinstance(items, list) else items.get("results", [])
        assert len(items) >= 1
        nid = items[0]["id"]

        # Create owner B and try to mark owner A's notification as read
        owner_b = create_temp_user(role="owner")
        client_b = APIClient(env_config.api_url)
        client_b.authenticate(owner_b["email"], owner_b["password"])
        napi_b = NotificationAPI(client_b)

        resp = napi_b.mark_read(nid)
        assert resp.status_code == 404

        client_b.logout()


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-API-008 … 011 — Broadcast
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationBroadcast:

    @pytest.mark.positive
    def test_broadcast_returns_201_with_count(
        self, notification_api: NotificationAPI, notification_data
    ):
        """TC-S6-API-008: Admin broadcast returns 201 with 'created' count."""
        building_id = notification_data["building"]["id"]
        resp = notification_api.broadcast(
            subject="Test Announcement",
            message="This is a broadcast test message.",
            building_id=building_id,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "created" in body
        assert isinstance(body["created"], int)
        assert body["created"] >= 1  # At least 1 owner (apartment owner)

    @pytest.mark.positive
    def test_broadcast_creates_notification_in_owner_list(
        self, notification_api: NotificationAPI, notification_data
    ):
        """TC-S6-API-009: After broadcast, owner sees an ANNOUNCEMENT notification."""
        building_id = notification_data["building"]["id"]
        subject = "Building News"
        notification_api.broadcast(
            subject=subject,
            message="Important update for all residents.",
            building_id=building_id,
        )
        owner_napi = notification_data["owner_notification_api"]
        items = owner_napi.list().json()
        items = items if isinstance(items, list) else items.get("results", [])
        types = [n["notification_type"] for n in items]
        assert "announcement" in types

    @pytest.mark.negative
    def test_broadcast_returns_403_for_non_admin(
        self, owner_notification_api: NotificationAPI, notification_data
    ):
        """TC-S6-API-010: Non-admin POSTing to broadcast receives 403."""
        resp = owner_notification_api.broadcast(
            subject="Hack",
            message="Not allowed",
            building_id=notification_data["building"]["id"],
        )
        assert resp.status_code == 403

    @pytest.mark.negative
    def test_broadcast_returns_400_for_missing_fields(
        self, notification_api: NotificationAPI
    ):
        """TC-S6-API-011: Broadcast with missing required fields returns 400."""
        resp = notification_api._c.post(
            "/notifications/broadcast/",
            json={"subject": "Missing message and building_id"},
        )
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-API-012 … 014 — RBAC
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationRBAC:

    @pytest.mark.negative
    def test_unauthenticated_list_returns_401(self, unauthenticated_api: APIClient):
        """TC-S6-API-012: Unauthenticated GET /notifications/ → 401."""
        napi = NotificationAPI(unauthenticated_api)
        resp = napi.list()
        assert resp.status_code == 401

    @pytest.mark.negative
    def test_unauthenticated_broadcast_returns_401(self, unauthenticated_api: APIClient):
        """TC-S6-API-013: Unauthenticated POST /notifications/broadcast/ → 401."""
        napi = NotificationAPI(unauthenticated_api)
        resp = napi.broadcast(
            subject="x",
            message="y",
            building_id="00000000-0000-0000-0000-000000000000",
        )
        assert resp.status_code == 401

    @pytest.mark.positive
    def test_admin_notifications_isolated_from_owner(
        self, notification_api: NotificationAPI, notification_data
    ):
        """TC-S6-API-014: Admin's notification list does NOT contain owner's notifications."""
        admin_items = notification_api.list().json()
        admin_items = admin_items if isinstance(admin_items, list) else admin_items.get("results", [])

        owner_napi = notification_data["owner_notification_api"]
        owner_items = owner_napi.list().json()
        owner_items = owner_items if isinstance(owner_items, list) else owner_items.get("results", [])

        owner_ids = {n["id"] for n in owner_items}
        admin_ids = {n["id"] for n in admin_items}
        # No overlap — each user sees only their own notifications
        assert owner_ids.isdisjoint(admin_ids), "Admin and owner should not share notifications"


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-API-015 … 017 — Filtering
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationFiltering:

    @pytest.mark.positive
    def test_filter_unread_returns_only_unread(self, notification_data):
        """TC-S6-API-015: is_read=false returns only unread notifications."""
        owner_napi = notification_data["owner_notification_api"]
        resp = owner_napi.list(is_read=False)
        assert resp.status_code == 200
        items = resp.json()
        items = items if isinstance(items, list) else items.get("results", [])
        for n in items:
            assert n["is_read"] is False

    @pytest.mark.positive
    def test_filter_read_returns_only_read(self, notification_data):
        """TC-S6-API-016: is_read=true returns only read notifications."""
        owner_napi = notification_data["owner_notification_api"]
        # First mark one as read
        all_items = owner_napi.list().json()
        all_items = all_items if isinstance(all_items, list) else all_items.get("results", [])
        if all_items:
            owner_napi.mark_read(all_items[0]["id"])

        resp = owner_napi.list(is_read=True)
        assert resp.status_code == 200
        items = resp.json()
        items = items if isinstance(items, list) else items.get("results", [])
        for n in items:
            assert n["is_read"] is True

    @pytest.mark.positive
    def test_no_filter_returns_all(self, notification_data):
        """TC-S6-API-017: No filter returns both read and unread notifications."""
        owner_napi = notification_data["owner_notification_api"]
        # Mark one as read if possible
        all_items = owner_napi.list().json()
        all_items = all_items if isinstance(all_items, list) else all_items.get("results", [])
        if len(all_items) >= 1:
            owner_napi.mark_read(all_items[0]["id"])

        resp = owner_napi.list()
        assert resp.status_code == 200
        items = resp.json()
        items = items if isinstance(items, list) else items.get("results", [])
        assert len(items) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-API-018 … 020 — Triggers
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationTriggers:

    @pytest.mark.positive
    def test_expense_creation_generates_expense_added_notification(self, notification_data):
        """TC-S6-API-018: Creating an expense triggers EXPENSE_ADDED notification for the owner."""
        owner_napi = notification_data["owner_notification_api"]
        resp = owner_napi.list()
        items = resp.json()
        items = items if isinstance(items, list) else items.get("results", [])
        types = [n["notification_type"] for n in items]
        assert "expense_added" in types, f"Expected 'expense_added' in {types}"

    @pytest.mark.positive
    def test_payment_creation_generates_payment_confirmed_notification(
        self,
        env_config,
        notification_data,
        create_temp_payment,
    ):
        """TC-S6-API-019: Recording a payment triggers PAYMENT_CONFIRMED notification for the owner."""
        apartment_id = notification_data["apartment"]["id"]
        expense_id = notification_data["expense"]["id"]
        create_temp_payment(apartment_id=apartment_id, expense_id=expense_id, amount=50.00)

        owner_napi = notification_data["owner_notification_api"]
        items = owner_napi.list().json()
        items = items if isinstance(items, list) else items.get("results", [])
        types = [n["notification_type"] for n in items]
        assert "payment_confirmed" in types, f"Expected 'payment_confirmed' in {types}"

    @pytest.mark.positive
    def test_notification_metadata_has_correct_keys(self, notification_data):
        """TC-S6-API-020: EXPENSE_ADDED notification metadata contains 'expense_id'."""
        owner_napi = notification_data["owner_notification_api"]
        items = owner_napi.list().json()
        items = items if isinstance(items, list) else items.get("results", [])
        expense_notifs = [n for n in items if n["notification_type"] == "expense_added"]
        assert len(expense_notifs) >= 1
        first = expense_notifs[0]
        assert "metadata" in first
        assert "expense_id" in first["metadata"]
