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


@pytest.mark.django_db
class TestInviteHardening:
    def _invite(self, admin_client, unit, email=""):
        return admin_client.post(f"/api/v1/apartments/{unit.id}/invite/", {"email": email}, format="json").data

    def test_invite_for_an_email_cannot_be_redeemed_by_someone_else(self, api_client, admin_client, owner_user, unit):
        invite = self._invite(admin_client, unit, email="someone-else@abem.test")
        api_client.force_authenticate(owner_user)
        resp = api_client.post("/api/v1/apartments/invite/use/", {"token": invite["token"]}, format="json")
        assert resp.status_code == 403
        unit.refresh_from_db()
        assert unit.owner is None

    def test_invite_for_an_email_works_for_that_account(self, api_client, admin_client, owner_user, unit):
        invite = self._invite(admin_client, unit, email=owner_user.email.upper())
        api_client.force_authenticate(owner_user)
        resp = api_client.post("/api/v1/apartments/invite/use/", {"token": invite["token"]}, format="json")
        assert resp.status_code == 200

    def test_malformed_token_is_404_not_500(self, api_client):
        assert api_client.get("/api/v1/apartments/invite/validate/", {"token": "not-a-uuid"}).status_code == 404

    def test_code_lookup_does_not_reveal_the_invited_email(self, api_client, admin_client, unit):
        invite = self._invite(admin_client, unit, email="private@abem.test")
        by_code = api_client.get("/api/v1/apartments/invite/validate/", {"code": invite["registration_code"]})
        by_token = api_client.get("/api/v1/apartments/invite/validate/", {"token": invite["token"]})
        assert by_code.data["invited_email"] == ""
        assert by_token.data["invited_email"] == "private@abem.test"
