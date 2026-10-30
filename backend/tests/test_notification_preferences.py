"""People can switch kinds of notification off; reminders and announcements respect it."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding
from apps.expenses.models import ApartmentExpense, Expense, ExpenseCategory
from apps.notifications.reminders import send_payment_reminders

pytestmark = pytest.mark.django_db
TODAY = date(2026, 11, 10)


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def overdue(admin_user, owner_user):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    unit = Apartment.objects.create(building=building, unit_number="1", owner=owner_user)
    unit.owners.add(owner_user)
    UserBuilding.objects.create(user=owner_user, building=building)
    category = ExpenseCategory.objects.create(building=building, name="Lift")
    expense = Expense.objects.create(building=building, category=category, title="Lift", amount=Decimal("100.00"),
                                     expense_date=TODAY - timedelta(days=30), due_date=TODAY - timedelta(days=1), created_by=admin_user)
    ApartmentExpense.objects.create(expense=expense, apartment=unit, share_amount=Decimal("100.00"))
    return unit


def _prefs(user, prefs):
    return _client(user).patch("/api/v1/auth/profile/", {"notification_preferences": prefs}, format="json")


def test_everything_is_on_by_default(owner_user, overdue):
    assert send_payment_reminders(TODAY)["overdue"] == 1
    assert owner_user.notifications.count() == 1 and len(mail.outbox) == 1


def test_switching_off_payment_reminders_silences_both_app_and_email(owner_user, overdue):
    assert _prefs(owner_user, {"payment_reminders": False}).status_code == 200
    send_payment_reminders(TODAY)
    assert owner_user.notifications.count() == 0 and mail.outbox == []


def test_switching_off_email_keeps_the_in_app_reminder(owner_user, overdue):
    _prefs(owner_user, {"email": False})
    send_payment_reminders(TODAY)
    assert owner_user.notifications.count() == 1 and mail.outbox == []


def test_preferences_are_returned_with_the_profile(owner_user):
    _prefs(owner_user, {"announcements": False})
    assert _client(owner_user).get("/api/v1/auth/profile/").data["notification_preferences"] == {"announcements": False}


def test_unknown_switches_and_non_boolean_values_are_refused(owner_user):
    assert _prefs(owner_user, {"spam": True}).status_code == 400
    assert _prefs(owner_user, {"email": "no"}).status_code == 400
    assert _prefs(owner_user, ["email"]).status_code == 400


def test_polls_respect_the_announcements_switch(admin_user, overdue, owner_user):
    from django.utils import timezone

    _prefs(owner_user, {"announcements": False})
    resp = _client(admin_user).post("/api/v1/governance/polls/", {
        "building_id": str(overdue.building_id), "title": "Paint the hall?", "options": ["Yes", "No"],
        "closes_at": (timezone.now() + timedelta(days=2)).isoformat()}, format="json")
    assert resp.status_code == 201 and owner_user.notifications.count() == 0
