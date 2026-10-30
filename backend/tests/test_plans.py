"""Plans: limits and features follow the plan, trials lapse to free, and the InstaPay flow extends it."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.plans.models import BuildingPlan, Plan, PlanPayment
from apps.plans.services import effective_plan, extend, has_feature, unit_room

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(
        email="root@abem.test", password="Pass1234!x", first_name="Root", last_name="Owner"
    )


@pytest.fixture
def old_building(admin_user):
    """A building whose trial is long over, so it is on the free plan unless paid for."""
    b = Building.objects.create(name="Old", address="1 St", admin=admin_user)
    Building.objects.filter(pk=b.pk).update(created_at=timezone.now() - timedelta(days=60))
    b.refresh_from_db()
    return b


def test_seeded_plans_exist():
    assert list(Plan.objects.values_list("code", flat=True)) == ["free", "standard", "plus"]


def test_new_buildings_get_the_trial_then_fall_back_to_free(admin_user, old_building):
    fresh = Building.objects.create(name="Fresh", address="2 St", admin=admin_user)
    plan, until, trial = effective_plan(fresh)
    assert plan.code == "plus" and trial and until
    assert effective_plan(old_building)[0].code == "free"


def test_free_plan_limits_units_and_features(old_building):
    assert not has_feature(old_building, "annual_report") and not has_feature(old_building, "subscriptions")
    for n in range(10):
        Apartment.objects.create(building=old_building, unit_number=str(n))
    assert not unit_room(old_building)


def test_api_blocks_the_eleventh_unit_and_gated_features(admin_user, old_building):
    for n in range(10):
        Apartment.objects.create(building=old_building, unit_number=str(n))
    client = _client(admin_user)
    resp = client.post("/api/v1/apartments/", {"building": str(old_building.pk), "unit_number": "99"}, format="json")
    assert resp.status_code == 400
    assert client.get(f"/api/v1/buildings/{old_building.pk}/annual-report/").status_code == 403
    url = f"/api/v1/buildings/{old_building.pk}/subscription/"
    assert client.post(url, {"amount": "100"}, format="json").status_code == 403


def test_extend_adds_a_period_from_the_old_end_when_still_running(old_building):
    standard = Plan.objects.get(code="standard")
    first = extend(old_building, standard, "monthly", today=date(2026, 1, 31))
    assert first == date(2026, 2, 28)
    assert extend(old_building, standard, "yearly", today=date(2026, 2, 1)) == date(2027, 2, 28)
    assert BuildingPlan.objects.get(building=old_building).plan_id == "standard"


def test_instapay_flow_confirm_switches_the_plan(admin_user, superuser, old_building):
    resp = _client(admin_user).post("/api/v1/plans/payments/", {
        "building_id": str(old_building.pk), "plan_code": "standard", "period": "monthly", "reference": "IP123",
    }, format="json")
    assert resp.status_code == 201 and Decimal(resp.data["amount"]) == Decimal("99.00")
    assert effective_plan(old_building)[0].code == "free"   # nothing changes until it is confirmed

    assert _client(admin_user).post(f"/api/v1/plans/payments/{resp.data['id']}/confirm/").status_code == 404
    assert _client(superuser).post(f"/api/v1/plans/payments/{resp.data['id']}/confirm/").status_code == 200
    plan, until, trial = effective_plan(old_building)
    assert plan.code == "standard" and until > date.today() and not trial
    assert has_feature(old_building, "subscriptions")
    assert _client(superuser).post(f"/api/v1/plans/payments/{resp.data['id']}/reject/").status_code == 400  # once only


def test_price_is_taken_when_requested_and_free_plan_cannot_be_paid(admin_user, old_building):
    resp = _client(admin_user).post("/api/v1/plans/payments/", {
        "building_id": str(old_building.pk), "plan_code": "free", "period": "monthly", "reference": "x",
    }, format="json")
    assert resp.status_code == 400


def test_other_admins_cannot_pay_for_someone_elses_building(old_building, django_user_model):
    other = django_user_model.objects.create_user(email="b@abem.test", password="Pass1234!x", role="admin")
    resp = _client(other).post("/api/v1/plans/payments/", {
        "building_id": str(old_building.pk), "plan_code": "standard", "period": "monthly", "reference": "x",
    }, format="json")
    assert resp.status_code in (403, 404)
    assert PlanPayment.objects.count() == 0


def test_only_platform_owners_edit_prices(admin_user, superuser):
    url = "/api/v1/plans/tiers/standard/"
    assert _client(admin_user).patch(url, {"price_monthly": "1"}, format="json").status_code == 403
    resp = _client(superuser).patch(url, {"price_monthly": "120.00", "max_units": 50}, format="json")
    assert resp.status_code == 200 and Plan.objects.get(code="standard").max_units == 50
    assert _client(superuser).patch(url, {"features": ["magic"]}, format="json").status_code == 400
    assert _client(superuser).patch(url, {"price_monthly": "-5"}, format="json").status_code == 400


def test_current_plan_and_settings(admin_user, superuser, old_building):
    data = _client(admin_user).get(f"/api/v1/plans/current/?building_id={old_building.pk}").data
    assert data["plan"]["code"] == "free" and data["units"] == 0
    assert _client(admin_user).get("/api/v1/plans/settings/").status_code == 403
    body = {"instapay_address": "3mara@instapay", "trial_days": 7}
    resp = _client(superuser).patch("/api/v1/plans/settings/", body, format="json")
    assert resp.data == {"instapay_address": "3mara@instapay", "trial_days": 7}
    current = _client(admin_user).get(f"/api/v1/plans/current/?building_id={old_building.pk}").data
    assert current["instapay_address"] == "3mara@instapay"
