"""R-28: nobody confirms or rejects a payment claim for a unit they own or rent."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def setup(admin_user, owner_user, django_user_model):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    UserBuilding.objects.create(user=owner_user, building=building)
    other = django_user_model.objects.create_user(email="o2@abem.test", password="Passw0rd!x", role="owner")
    UserBuilding.objects.create(user=other, building=building)
    # the admin also lives in unit 1 together with owner_user
    mine = Apartment.objects.create(building=building, unit_number="1", owner=owner_user, balance=Decimal("300.00"))
    mine.owners.add(owner_user, admin_user)
    theirs = Apartment.objects.create(building=building, unit_number="2", owner=other, balance=Decimal("300.00"))
    theirs.owners.add(other)
    return {"mine": mine, "theirs": theirs, "other": other}


def _claim(user, unit):
    resp = _client(user).post(
        "/api/v1/payments/claims/", {"apartment_id": str(unit.pk), "amount": "100.00", "reference": "r"}, format="json"
    )
    assert resp.status_code == 201
    return resp.data["id"]


def test_admin_cannot_confirm_or_reject_a_claim_for_their_own_unit(admin_user, owner_user, setup):
    first, second = _claim(owner_user, setup["mine"]), _claim(owner_user, setup["mine"])
    client = _client(admin_user)
    assert client.post(f"/api/v1/payments/claims/{first}/confirm/").status_code == 403
    assert client.post(f"/api/v1/payments/claims/{second}/reject/").status_code == 403
    setup["mine"].refresh_from_db()
    assert setup["mine"].balance == Decimal("300.00") and not Payment.objects.exists()


def test_admin_still_reviews_other_units(admin_user, setup):
    claim = _claim(setup["other"], setup["theirs"])
    assert _client(admin_user).post(f"/api/v1/payments/claims/{claim}/confirm/").status_code == 200


def test_treasurer_cannot_review_their_own_unit(admin_user, owner_user, setup):
    UserBuilding.objects.filter(user=setup["other"]).update(board_role="treasurer")
    claim = _claim(setup["other"], setup["theirs"])
    assert _client(setup["other"]).post(f"/api/v1/payments/claims/{claim}/confirm/").status_code == 403
    # but the treasurer can review a neighbour's claim
    neighbour = _claim(owner_user, setup["mine"])
    assert _client(setup["other"]).post(f"/api/v1/payments/claims/{neighbour}/confirm/").status_code == 200
