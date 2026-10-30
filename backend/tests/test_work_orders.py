"""Work orders: a maintenance report taken on by a contractor, its cost linked, the resident informed."""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.buildings.models import Building, UserBuilding
from apps.expenses.models import Expense, ExpenseCategory
from apps.maintenance.models import MaintenanceReport
from apps.operations.models import Contractor

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


@pytest.fixture
def resident(building, owner_user):
    UserBuilding.objects.create(user=owner_user, building=building)
    return owner_user


@pytest.fixture
def report(building, resident):
    return MaintenanceReport.objects.create(building=building, reporter=resident, category="elevator", description="Stuck")


@pytest.fixture
def contractor(building):
    return Contractor.objects.create(building=building, name="Ahmed", trade="Elevators")


def _create(user, report, contractor=None, **extra):
    data = {"report_id": str(report.pk), "scheduled_on": "2026-11-20", **extra}
    if contractor:
        data["contractor_id"] = str(contractor.pk)
    return _client(user).post("/api/v1/maintenance/work-orders/", data, format="json")


def test_admin_takes_a_report_on_and_the_resident_sees_it(admin_user, resident, report, contractor):
    resp = _create(admin_user, report, contractor)
    assert resp.status_code == 201
    mine = _client(resident).get("/api/v1/maintenance/").data["results"][0]
    assert mine["status"] == "in_progress"
    assert mine["work_order"]["contractor_name"] == "Ahmed" and mine["work_order"]["scheduled_on"] == "2026-11-20"
    assert mine["work_order"]["cost"] is None


def test_finishing_the_order_finishes_the_report_and_tells_the_reporter(admin_user, resident, report, contractor):
    order_id = _create(admin_user, report, contractor).data["id"]
    resp = _client(admin_user).patch(f"/api/v1/maintenance/work-orders/{order_id}/", {"status": "done"}, format="json")
    assert resp.status_code == 200 and resp.data["completed_on"] is not None
    report.refresh_from_db()
    assert report.status == "done"
    assert resident.notifications.filter(metadata__report_id=str(report.pk)).count() == 1


def test_the_cost_is_linked_to_an_expense_of_the_same_building(admin_user, building, resident, report, contractor):
    category = ExpenseCategory.objects.create(building=building, name="Lift")
    expense = Expense.objects.create(building=building, category=category, title="Lift repair", amount=Decimal("750.00"),
                                     expense_date=date(2026, 11, 21), created_by=admin_user)
    order_id = _create(admin_user, report, contractor).data["id"]
    resp = _client(admin_user).patch(f"/api/v1/maintenance/work-orders/{order_id}/", {"expense_id": str(expense.pk)}, format="json")
    assert resp.status_code == 200
    assert _client(resident).get("/api/v1/maintenance/").data["results"][0]["work_order"]["cost"] == "750.00"


def test_foreign_contractors_and_expenses_are_refused(admin_user, building, report):
    other = Building.objects.create(name="Other", address="9 Elm", admin=admin_user)
    foreign = Contractor.objects.create(building=other, name="Elsewhere")
    assert _create(admin_user, report, foreign).status_code == 400
    category = ExpenseCategory.objects.create(building=other, name="X")
    expense = Expense.objects.create(building=other, category=category, title="E", amount=Decimal("5.00"), expense_date=date(2026, 11, 1), created_by=admin_user)
    order_id = _create(admin_user, report).data["id"]
    assert _client(admin_user).patch(f"/api/v1/maintenance/work-orders/{order_id}/", {"expense_id": str(expense.pk)}, format="json").status_code == 400


def test_board_members_can_manage_orders_but_residents_cannot(building, resident, report, django_user_model):
    secretary = django_user_model.objects.create_user(email="sec@abem.test", password="SPass1!xxx", role="owner")
    UserBuilding.objects.create(user=secretary, building=building, board_role="secretary")
    assert _create(resident, report).status_code == 403
    assert _create(secretary, report).status_code == 201


def test_other_buildings_cannot_see_or_change_the_order(admin_user, report, django_user_model):
    order_id = _create(admin_user, report).data["id"]
    outsider = django_user_model.objects.create_user(email="o@abem.test", password="OPass1!xxx", role="admin")
    assert _client(outsider).patch(f"/api/v1/maintenance/work-orders/{order_id}/", {"status": "done"}, format="json").status_code == 404
    assert _create(outsider, report).status_code == 403


def test_one_order_per_report(admin_user, report):
    assert _create(admin_user, report).status_code == 201
    assert _create(admin_user, report).status_code == 400
