from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import Expense, ExpenseCategory, RecurringConfig
from apps.expenses.recurring import generate_recurring_expenses
from apps.expenses.utils import run_split_engine

pytestmark = pytest.mark.django_db


@pytest.fixture
def template(admin_user):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    Apartment.objects.create(building=building, unit_number="1")
    Apartment.objects.create(building=building, unit_number="2")
    category = ExpenseCategory.objects.create(building=building, name="Cleaning")
    expense = Expense.objects.create(
        building=building, category=category, title="Cleaning", amount=Decimal("200.00"),
        expense_date=date.today() - timedelta(days=40), is_recurring=True, created_by=admin_user,
    )
    run_split_engine(expense)
    return expense


def test_due_recurring_expense_is_copied_and_rescheduled(template):
    config = RecurringConfig.objects.create(
        expense=template, frequency="monthly", next_due=date.today() - timedelta(days=1)
    )
    assert generate_recurring_expenses() == 1

    copy = Expense.objects.exclude(pk=template.pk).get()
    assert copy.title == "Cleaning" and copy.amount == Decimal("200.00") and not copy.is_recurring
    assert copy.apartment_expenses.count() == 2
    config.refresh_from_db()
    assert config.next_due > date.today()


def test_nothing_is_created_before_the_due_date(template):
    RecurringConfig.objects.create(expense=template, frequency="monthly", next_due=date.today() + timedelta(days=5))
    assert generate_recurring_expenses() == 0
    assert Expense.objects.count() == 1


def test_management_command_runs_the_job(template, capsys):
    from django.core.management import call_command

    RecurringConfig.objects.create(expense=template, frequency="monthly", next_due=date.today())
    call_command("generate_recurring_expenses")
    assert "Created 1 recurring expense" in capsys.readouterr().out
    assert Expense.objects.count() == 2
