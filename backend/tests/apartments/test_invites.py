"""Shareable unit-invite links: email is optional, the link is one-time."""
import pytest
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment, UnitInvitation
from apps.buildings.models import Building

User = get_user_model()


@pytest.fixture
def unit(db, admin_user):
    building = Building.objects.create(name="Building 5", address="1 Nile St", admin=admin_user)
    return Apartment.objects.create(building=building, unit_number="3A")


@pytest.mark.django_db
class TestShareableInvite:
    def test_admin_can_create_invite_without_email(self, admin_client, unit):
        resp = admin_client.post(f"/api/v1/apartments/{unit.id}/invite/", {}, format="json")
        assert resp.status_code == 201
        assert resp.data["token"] and resp.data["registration_code"]
        assert resp.data["invited_email"] == ""

    def test_invalid_email_is_rejected(self, admin_client, unit):
        resp = admin_client.post(f"/api/v1/apartments/{unit.id}/invite/", {"email": "nope"}, format="json")
        assert resp.status_code == 400

    def test_new_shareable_invite_retires_the_previous_one(self, admin_client, unit):
        first = admin_client.post(f"/api/v1/apartments/{unit.id}/invite/", {}, format="json").data["token"]
        admin_client.post(f"/api/v1/apartments/{unit.id}/invite/", {}, format="json")
        assert not UnitInvitation.objects.get(token=first).is_valid

    def test_owner_can_claim_unit_with_shared_link_once(self, api_client, admin_client, owner_user, unit):
        token = admin_client.post(f"/api/v1/apartments/{unit.id}/invite/", {}, format="json").data["token"]

        # public validation shows the unit without logging in
        info = api_client.get("/api/v1/apartments/invite/validate/", {"token": token})
        assert info.status_code == 200 and info.data["unit_number"] == "3A"

        api_client.force_authenticate(owner_user)
        assert api_client.post("/api/v1/apartments/invite/use/", {"token": token}, format="json").status_code == 200
        unit.refresh_from_db()
        assert unit.owner == owner_user

        # one-time: the same link cannot be used again
        again = api_client.get("/api/v1/apartments/invite/validate/", {"token": token})
        assert again.status_code == 410
