"""R-27: a building can have only one pending plan payment; confirming extends the plan once."""

import pytest
from rest_framework.test import APIClient

from apps.buildings.models import Building
from apps.plans.models import BuildingPlan, PlanPayment

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


def _body(building, **extra):
    return {"building_id": str(building.pk), "plan_code": "standard", "period": "monthly", "reference": "x", **extra}


def test_second_pending_payment_is_refused(admin_user, building):
    client = _client(admin_user)
    assert client.post("/api/v1/plans/payments/", _body(building), format="json").status_code == 201
    resp = client.post("/api/v1/plans/payments/", _body(building, reference="y"), format="json")
    assert resp.status_code in (400, 409)
    assert PlanPayment.objects.filter(building=building).count() == 1


def test_new_payment_allowed_after_the_pending_one_is_reviewed(admin_user, building, django_user_model):
    root = django_user_model.objects.create_superuser(email="root@abem.test", password="Pass1234!x")
    first = _client(admin_user).post("/api/v1/plans/payments/", _body(building), format="json").data["id"]
    assert _client(root).post(f"/api/v1/plans/payments/{first}/reject/").status_code == 200
    assert _client(admin_user).post("/api/v1/plans/payments/", _body(building), format="json").status_code == 201


def test_confirming_twice_extends_the_plan_once(admin_user, building, django_user_model):
    root = django_user_model.objects.create_superuser(email="root@abem.test", password="Pass1234!x")
    pid = _client(admin_user).post("/api/v1/plans/payments/", _body(building), format="json").data["id"]
    assert _client(root).post(f"/api/v1/plans/payments/{pid}/confirm/").status_code == 200
    until = BuildingPlan.objects.get(building=building).paid_until
    assert _client(root).post(f"/api/v1/plans/payments/{pid}/confirm/").status_code == 400
    assert BuildingPlan.objects.get(building=building).paid_until == until
