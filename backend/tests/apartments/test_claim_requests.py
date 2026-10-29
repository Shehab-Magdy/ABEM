"""Residents ask to claim a unit; the building's admin approves."""
import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def unit(admin_user):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    return Apartment.objects.create(building=building, unit_number="4B")


def _claim(user, unit):
    return _client(user).post(f"/api/v1/apartments/{unit.pk}/claim/")


def test_resident_claim_waits_for_approval(owner_user, admin_user, unit):
    resp = _claim(owner_user, unit)
    assert resp.status_code == 202 and resp.data["status"] == "pending"
    unit.refresh_from_db()
    assert unit.owner is None and not unit.owners.exists()
    assert not owner_user.buildings.exists()  # no access to the building yet

    pending = _client(admin_user).get("/api/v1/apartments/claim-requests/", {"status": "pending"}).data["results"]
    assert len(pending) == 1 and pending[0]["user_email"] == owner_user.email


def test_admin_approves_and_resident_becomes_owner(owner_user, admin_user, unit):
    _claim(owner_user, unit)
    req_id = _client(admin_user).get("/api/v1/apartments/claim-requests/").data["results"][0]["id"]
    resp = _client(admin_user).post(f"/api/v1/apartments/claim-requests/{req_id}/approve/")
    assert resp.status_code == 200 and resp.data["status"] == "approved"
    unit.refresh_from_db()
    assert unit.owner == owner_user and unit.owners.filter(pk=owner_user.pk).exists()
    assert owner_user.buildings.filter(pk=unit.building_id).exists()
    assert _client(admin_user).post(f"/api/v1/apartments/claim-requests/{req_id}/approve/").status_code == 409


def test_rejected_claim_gives_no_access(owner_user, admin_user, unit):
    _claim(owner_user, unit)
    req_id = _client(admin_user).get("/api/v1/apartments/claim-requests/").data["results"][0]["id"]
    assert _client(admin_user).post(f"/api/v1/apartments/claim-requests/{req_id}/reject/").status_code == 200
    unit.refresh_from_db()
    assert unit.owner is None and not owner_user.buildings.exists()


def test_asking_twice_is_a_conflict(owner_user, unit):
    assert _claim(owner_user, unit).status_code == 202
    assert _claim(owner_user, unit).status_code == 409


def test_residents_cannot_approve_and_other_admins_cannot_see(owner_user, unit, django_user_model):
    _claim(owner_user, unit)
    req_id = _client(owner_user).get("/api/v1/apartments/claim-requests/").data["results"][0]["id"]
    assert _client(owner_user).post(f"/api/v1/apartments/claim-requests/{req_id}/approve/").status_code == 403
    other = django_user_model.objects.create_user(email="b@abem.test", password="Pass1234!x", role="admin")
    assert _client(other).get("/api/v1/apartments/claim-requests/").data["results"] == []
    assert _client(other).post(f"/api/v1/apartments/claim-requests/{req_id}/approve/").status_code == 404


def test_building_admin_can_still_claim_directly(admin_user, unit):
    resp = _claim(admin_user, unit)
    assert resp.status_code == 200
    unit.refresh_from_db()
    assert unit.owner == admin_user
