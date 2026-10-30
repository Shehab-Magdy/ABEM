"""Payment reminders: due soon, overdue, no duplicates, nothing for paid shares."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.core.management import call_command

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import ApartmentExpense, Expense, ExpenseCategory
from apps.notifications.models import Notification, NotificationType, ReminderLog
from apps.notifications.reminders import send_payment_reminders
from apps.payments.models import Payment, PaymentExpense

pytestmark = pytest.mark.django_db

TODAY = date(2026, 11, 10)


@pytest.fixture
def unit(admin_user, owner_user):
    owner_user.preferred_language = "ar"
    owner_user.save()
    building = Building.objects.create(name="عمارة ٥", address="1 Nile St", admin=admin_user)
    apt = Apartment.objects.create(building=building, unit_number="3", owner=owner_user)
    apt.owners.add(owner_user)
    return apt


def _expense(unit, admin_user, due, amount="100.00", **extra):
    category, _ = ExpenseCategory.objects.get_or_create(building=unit.building, name="Lift")
    expense = Expense.objects.create(
        building=unit.building, category=category, title="Lift", amount=Decimal(amount),
        expense_date=TODAY - timedelta(days=30), due_date=due, created_by=admin_user, **extra,
    )
    ApartmentExpense.objects.create(expense=expense, apartment=unit, share_amount=Decimal(amount))
    return expense


def test_share_due_in_three_days_gets_one_reminder(unit, admin_user, owner_user):
    _expense(unit, admin_user, TODAY + timedelta(days=3))
    counts = send_payment_reminders(TODAY)
    assert counts["due_soon"] == 1 and counts["overdue"] == 0
    note = Notification.objects.get(user=owner_user)
    assert note.notification_type == NotificationType.PAYMENT_DUE
    assert "100.00" in note.body and "ج.م." in note.body  # owner prefers Arabic
    assert len(mail.outbox) == 1 and mail.outbox[0].to == [owner_user.email]


def test_not_reminded_twice_the_same_day_or_again_before_due(unit, admin_user):
    _expense(unit, admin_user, TODAY + timedelta(days=3))
    send_payment_reminders(TODAY)
    assert send_payment_reminders(TODAY)["due_soon"] == 0
    assert send_payment_reminders(TODAY + timedelta(days=1))["due_soon"] == 0
    assert ReminderLog.objects.count() == 1


def test_far_future_due_dates_are_left_alone(unit, admin_user):
    _expense(unit, admin_user, TODAY + timedelta(days=4))
    assert send_payment_reminders(TODAY) == {"due_soon": 0, "overdue": 0, "skipped": 0, "emails_failed": 0}


def test_overdue_share_is_reminded_then_weekly(unit, admin_user, owner_user):
    _expense(unit, admin_user, TODAY - timedelta(days=1))
    assert send_payment_reminders(TODAY)["overdue"] == 1
    assert send_payment_reminders(TODAY + timedelta(days=3))["overdue"] == 0   # too soon
    assert send_payment_reminders(TODAY + timedelta(days=7))["overdue"] == 1   # a week later
    assert Notification.objects.filter(user=owner_user, notification_type=NotificationType.PAYMENT_OVERDUE).count() == 2


def test_paid_and_manually_paid_shares_are_not_reminded(unit, admin_user):
    paid = _expense(unit, admin_user, TODAY - timedelta(days=1))
    payment = Payment.objects.create(
        apartment=unit, amount_paid=Decimal("100.00"), payment_date=TODAY, recorded_by=admin_user
    )
    PaymentExpense.objects.create(payment=payment, expense=paid, allocated_amount=Decimal("100.00"))
    _expense(unit, admin_user, TODAY - timedelta(days=1), is_manually_paid=True)
    assert send_payment_reminders(TODAY)["overdue"] == 0


def test_partly_paid_share_reminds_for_what_is_left(unit, admin_user, owner_user):
    expense = _expense(unit, admin_user, TODAY - timedelta(days=1))
    payment = Payment.objects.create(
        apartment=unit, amount_paid=Decimal("40.00"), payment_date=TODAY, recorded_by=admin_user
    )
    PaymentExpense.objects.create(payment=payment, expense=expense, allocated_amount=Decimal("40.00"))
    send_payment_reminders(TODAY)
    assert "60.00" in Notification.objects.get(user=owner_user).body


def test_expenses_without_a_due_date_and_deleted_ones_are_ignored(unit, admin_user):
    _expense(unit, admin_user, None)
    gone = _expense(unit, admin_user, TODAY - timedelta(days=2))
    gone.deleted_at = TODAY
    gone.save()
    assert send_payment_reminders(TODAY)["overdue"] == 0


def test_units_without_an_owner_are_skipped(admin_user):
    building = Building.objects.create(name="B", address="x", admin=admin_user)
    vacant = Apartment.objects.create(building=building, unit_number="9")
    _expense(vacant, admin_user, TODAY - timedelta(days=1))
    counts = send_payment_reminders(TODAY)
    assert counts["overdue"] == 0 and counts["skipped"] == 1


def test_management_command_runs(unit, admin_user, capsys):
    _expense(unit, admin_user, date.today() - timedelta(days=1))
    call_command("send_payment_reminders")
    assert "1 overdue" in capsys.readouterr().out
