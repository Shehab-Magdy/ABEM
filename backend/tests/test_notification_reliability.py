"""R-30: notification failures are logged, not swallowed; claim confirm and reject notify the resident."""

import logging
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding
from apps.expenses.models import ExpenseCategory
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def unit(admin_user, owner_user):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    UserBuilding.objects.create(user=owner_user, building=building)
    apt = Apartment.objects.create(building=building, unit_number="1", owner=owner_user, balance=Decimal("300.00"))
    apt.owners.add(owner_user)
    return apt


def _claim(owner_user, unit):
    resp = _client(owner_user).post(
        "/api/v1/payments/claims/", {"apartment_id": str(unit.pk), "amount": "100.00", "reference": "r"}, format="json"
    )
    return resp.data["id"]


def test_claim_confirm_notifies_the_resident(admin_user, owner_user, unit):
    claim = _claim(owner_user, unit)
    assert _client(admin_user).post(f"/api/v1/payments/claims/{claim}/confirm/").status_code == 200
    note = Notification.objects.get(user=owner_user, metadata__claim_id=claim)
    assert "100.00" in note.body


def test_claim_reject_notifies_the_resident_in_their_language(admin_user, owner_user, unit):
    owner_user.preferred_language = "ar"
    owner_user.save(update_fields=["preferred_language"])
    claim = _claim(owner_user, unit)
    assert _client(admin_user).post(f"/api/v1/payments/claims/{claim}/reject/").status_code == 200
    note = Notification.objects.get(user=owner_user, metadata__claim_id=claim)
    assert any("؀" <= ch <= "ۿ" for ch in note.title)


def test_payment_notification_failure_is_logged(admin_client, unit, monkeypatch, caplog):
    def boom(_payment):
        raise RuntimeError("push down")

    monkeypatch.setattr("apps.notifications.services.notify_payment_confirmed", boom)
    with caplog.at_level(logging.ERROR):
        resp = admin_client.post(
            "/api/v1/payments/",
            {"apartment_id": str(unit.pk), "amount_paid": "50.00", "payment_date": str(date.today()),
             "payment_method": "cash"},
            format="json",
        )
    assert resp.status_code == 201  # the payment still succeeds
    assert any(r.exc_info and "push down" in str(r.exc_info[1]) for r in caplog.records)


def test_expense_notification_failure_is_logged(admin_client, unit, monkeypatch, caplog):
    def boom(*_args):
        raise RuntimeError("inbox down")

    monkeypatch.setattr("apps.notifications.services.notify_expense_created", boom)
    category = ExpenseCategory.objects.create(building=unit.building, name="Lift")
    with caplog.at_level(logging.ERROR):
        resp = admin_client.post(
            "/api/v1/expenses/",
            {"building_id": str(unit.building_id), "category_id": str(category.pk), "title": "x", "amount": "100.00",
             "expense_date": str(date.today()), "split_type": "equal_all"},
            format="json",
        )
    assert resp.status_code == 201
    assert any(r.exc_info and "inbox down" in str(r.exc_info[1]) for r in caplog.records)
