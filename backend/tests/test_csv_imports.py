"""Bulk CSV import of units and expenses: preview first, then all-or-nothing."""
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import ApartmentExpense, Expense, ExpenseCategory

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user, num_floors=5)


def _csv(text, name="file.csv"):
    return SimpleUploadedFile(name, text.encode("utf-8-sig"), content_type="text/csv")


def _units(user, building, text, commit=False):
    return _client(user).post(f"/api/v1/buildings/{building.pk}/import-units/", {"file": _csv(text), "commit": "true" if commit else "false"}, format="multipart")


UNITS = "unit_number,type,floor,size_sqm\n1,apartment,1,95.5\n2,apartment,1,\nS1,store,0,40\n"


def test_preview_changes_nothing_and_reports_each_row(admin_user, building):
    resp = _units(admin_user, building, UNITS)
    assert resp.status_code == 200 and resp.data["total"] == 3 and resp.data["errors"] == 0 and resp.data["created"] == 0
    assert Apartment.objects.count() == 0


def test_commit_creates_all_units(admin_user, building):
    resp = _units(admin_user, building, UNITS, commit=True)
    assert resp.data["created"] == 3
    shop = Apartment.objects.get(unit_number="S1")
    assert shop.unit_type == "store" and Apartment.objects.get(unit_number="1").size_sqm == Decimal("95.50")


def test_one_bad_row_blocks_the_whole_import_and_says_why(admin_user, building):
    text = "unit_number,type,floor\n1,apartment,1\n1,apartment,1\n2,villa,1\n3,apartment,99\n4,apartment,x\n"
    resp = _units(admin_user, building, text, commit=True)
    assert resp.data["created"] == 0 and resp.data["errors"] == 4 and Apartment.objects.count() == 0
    problems = {r["row"]: r["problems"] for r in resp.data["rows"]}
    assert problems[2] == [] and "twice" in problems[3][0] and "apartment or store" in problems[4][0] and "between 0 and 5" in problems[5][0]


def test_existing_units_are_not_duplicated(admin_user, building):
    Apartment.objects.create(building=building, unit_number="1")
    resp = _units(admin_user, building, "unit_number\n1\n2\n", commit=True)
    assert resp.data["errors"] == 1 and Apartment.objects.count() == 1


def test_excel_style_files_work_semicolons_bom_and_arabic_types(admin_user, building):
    resp = _units(admin_user, building, "unit_number;type;floor\n1;شقة;1\nS1;محل;0\n", commit=True)
    assert resp.data["created"] == 2 and Apartment.objects.get(unit_number="S1").unit_type == "store"


def test_bad_files_are_refused_clearly(admin_user, building):
    assert _units(admin_user, building, "floor\n1\n").status_code == 400                       # missing unit_number
    assert _units(admin_user, building, "unit_number,colour\n1,red\n").status_code == 400      # unknown column
    assert _units(admin_user, building, "unit_number\n").status_code == 400                    # no rows
    assert _client(admin_user).post(f"/api/v1/buildings/{building.pk}/import-units/", {}, format="multipart").status_code == 400


def test_only_the_buildings_admin_can_import(building, owner_user, django_user_model):
    assert _units(owner_user, building, UNITS).status_code == 403
    other = django_user_model.objects.create_user(email="oa@abem.test", password="OPass1!xxx", role="admin")
    assert _units(other, building, UNITS).status_code == 404


@pytest.fixture
def stocked(building):
    for n in (1, 2):
        Apartment.objects.create(building=building, unit_number=str(n))
    return ExpenseCategory.objects.create(building=building, name="Cleaning")


def _expenses(user, building, text, commit=False):
    return _client(user).post("/api/v1/expenses/import/", {"building_id": str(building.pk), "file": _csv(text), "commit": "true" if commit else "false"}, format="multipart")


EXPENSES = "title,amount,date,category,split_type,due_date\nStairs cleaning,200,2026-10-01,Cleaning,equal_all,2026-10-15\nWindow cleaning,100,2026-10-02,cleaning,,\n"


def test_expenses_preview_then_commit_bills_the_units(admin_user, building, stocked):
    preview = _expenses(admin_user, building, EXPENSES)
    assert preview.data["errors"] == 0 and Expense.objects.count() == 0
    done = _expenses(admin_user, building, EXPENSES, commit=True)
    assert done.data["created"] == 2 and Expense.objects.count() == 2
    assert sum(a.balance for a in Apartment.objects.all()) == Decimal("300.00")
    assert ApartmentExpense.objects.count() == 4


def test_a_bad_expense_row_blocks_everything(admin_user, building, stocked):
    text = "title,amount,date,category\nOk,50,2026-10-01,Cleaning\nBad amount,abc,2026-10-01,Cleaning\nNo category,10,2026-10-01,Nope\nBad date,10,yesterday,Cleaning\n"
    resp = _expenses(admin_user, building, text, commit=True)
    assert resp.data["created"] == 0 and resp.data["errors"] == 3 and Expense.objects.count() == 0
    assert resp.data["rows"][0]["ok"] is True


def test_large_imported_costs_follow_the_approval_rule(admin_user, building, stocked):
    building.approval_threshold = Decimal("500.00")
    building.save()
    resp = _expenses(admin_user, building, "title,amount,date,category\nNew roof,9000,2026-10-01,Cleaning\n", commit=True)
    assert resp.data["created"] == 1 and Expense.objects.get().approval_status == "pending"
    assert sum(a.balance for a in Apartment.objects.all()) == Decimal("0.00")


def test_expense_import_is_admin_only_and_scoped(building, stocked, owner_user, django_user_model):
    assert _expenses(owner_user, building, EXPENSES).status_code == 403
    other = django_user_model.objects.create_user(email="oa@abem.test", password="OPass1!xxx", role="admin")
    assert _expenses(other, building, EXPENSES).status_code == 403


def test_residents_who_are_members_cannot_use_admin_only_building_actions(building, owner_user):
    """Regression: custom actions declared IsAdminRole, but the viewset ignored it for members of the building."""
    from apps.buildings.models import UserBuilding

    UserBuilding.objects.create(user=owner_user, building=building)
    c = _client(owner_user)
    assert c.post(f"/api/v1/buildings/{building.pk}/subscription/", {"amount": "999"}, format="json").status_code == 403
    assert c.get(f"/api/v1/buildings/{building.pk}/subscription/").status_code == 403
    assert _units(owner_user, building, UNITS).status_code == 403
    # ...while the read-only member views still work
    assert c.get(f"/api/v1/buildings/{building.pk}/treasury/").status_code == 200
    assert c.get(f"/api/v1/buildings/{building.pk}/statement/").status_code == 200
    assert c.get(f"/api/v1/buildings/{building.pk}/board/").status_code == 200
