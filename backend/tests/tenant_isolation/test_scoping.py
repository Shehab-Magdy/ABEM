"""An admin only sees and changes the buildings they manage."""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.apartments.models import Apartment
from apps.audit.models import AuditLog
from apps.buildings.models import Building
from apps.expenses.models import Expense, ExpenseCategory
from apps.payments.models import BuildingAsset, Payment

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


@pytest.fixture
def other_admin(django_user_model):
    return django_user_model.objects.create_user(
        email="admin-b@abem.test", password="AdminPass1!", first_name="B", last_name="Admin", role="admin"
    )


@pytest.fixture
def mine(admin_user):
    """Admin A's own building with one unit."""
    building = Building.objects.create(name="Mine", address="1 A St", admin=admin_user)
    unit = Apartment.objects.create(building=building, unit_number="1")
    return building, unit


@pytest.fixture
def theirs(other_admin):
    """Admin B's building with a unit, category, expense, payment and asset."""
    building = Building.objects.create(name="Theirs", address="2 B St", admin=other_admin)
    unit = Apartment.objects.create(building=building, unit_number="9")
    category = ExpenseCategory.objects.create(building=building, name="Lift")
    expense = Expense.objects.create(
        building=building, category=category, title="Lift repair", amount=Decimal("100.00"),
        expense_date=date.today(), created_by=other_admin,
    )
    payment = Payment.objects.create(
        apartment=unit, amount_paid=Decimal("50.00"), payment_date=date.today(), recorded_by=other_admin
    )
    asset = BuildingAsset.objects.create(building=building, name="Generator", created_by=other_admin)
    AuditLog.objects.create(user=other_admin, action="create", entity="expense", entity_id=expense.pk)
    return {"building": building, "unit": unit, "category": category, "expense": expense,
            "payment": payment, "asset": asset}


def _ids(resp):
    data = resp.data.get("results", resp.data) if hasattr(resp.data, "get") else resp.data
    return {str(row["id"]) for row in data}


@pytest.mark.parametrize("url,key", [
    ("/api/v1/apartments/", "unit"),
    ("/api/v1/expenses/", "expense"),
    ("/api/v1/expenses/categories/", "category"),
    ("/api/v1/payments/", "payment"),
    ("/api/v1/payments/assets/", "asset"),
])
def test_lists_exclude_other_admins_data(admin_client, mine, theirs, url, key):
    resp = admin_client.get(url)
    assert resp.status_code == 200
    assert str(theirs[key].pk) not in _ids(resp)


@pytest.mark.parametrize("url_tpl,key", [
    ("/api/v1/apartments/{}/", "unit"),
    ("/api/v1/expenses/{}/", "expense"),
    ("/api/v1/payments/{}/", "payment"),
    ("/api/v1/payments/assets/{}/", "asset"),
])
def test_detail_of_other_admins_data_is_404(admin_client, mine, theirs, url_tpl, key):
    assert admin_client.get(url_tpl.format(theirs[key].pk)).status_code == 404


def test_query_param_cannot_widen_scope(admin_client, mine, theirs):
    resp = admin_client.get("/api/v1/apartments/", {"building_id": str(theirs["building"].pk)})
    assert str(theirs["unit"].pk) not in _ids(resp)


def test_admin_sees_own_data(admin_client, mine):
    _, unit = mine
    assert str(unit.pk) in _ids(admin_client.get("/api/v1/apartments/"))


def test_co_admin_can_see_building(other_admin, mine, theirs):
    building, _ = mine
    building.co_admins.add(other_admin)
    assert str(mine[1].pk) in _ids(_client(other_admin).get("/api/v1/apartments/"))


def test_cannot_create_in_other_admins_building(admin_client, mine, theirs):
    building = str(theirs["building"].pk)
    assert admin_client.post(
        "/api/v1/apartments/", {"building_id": building, "unit_number": "X", "type": "apartment"}, format="json"
    ).status_code == 403
    assert admin_client.post(
        "/api/v1/expenses/categories/", {"building_id": building, "name": "Hack"}, format="json"
    ).status_code == 403
    assert admin_client.post(
        "/api/v1/payments/assets/", {"building_id": building, "name": "Hack"}, format="json"
    ).status_code == 403


def test_cannot_record_payment_for_other_admins_unit(admin_client, mine, theirs):
    resp = admin_client.post(
        "/api/v1/payments/",
        {"apartment_id": str(theirs["unit"].pk), "amount_paid": "10.00", "payment_date": str(date.today()),
         "payment_method": "cash"},
        format="json",
    )
    assert resp.status_code == 403
    theirs["unit"].refresh_from_db()
    assert theirs["unit"].balance == Decimal("0.00")


def test_users_building_filter_requires_managing_it(admin_client, mine, theirs):
    resp = admin_client.get("/api/v1/users/", {"building_id": str(theirs["building"].pk)})
    assert resp.status_code == 403


def test_audit_log_hides_other_admins_actions(admin_client, mine, theirs):
    resp = admin_client.get("/api/v1/audit/")
    assert resp.status_code == 200
    assert not any(row["entity_id"] == str(theirs["expense"].pk) for row in resp.data.get("results", resp.data))


@pytest.mark.parametrize("url,needle", [
    ("/api/v1/exports/expenses/", "Lift repair"),
    ("/api/v1/exports/payments/", "50.00"),
])
def test_exports_exclude_other_admins_data(admin_client, mine, theirs, url, needle):
    resp = admin_client.get(url)
    assert resp.status_code == 200
    body = b"".join(resp.streaming_content) if resp.streaming else resp.content
    assert needle.encode() not in body
