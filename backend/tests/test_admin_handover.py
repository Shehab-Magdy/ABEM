"""Hand a building over to a co-admin; primary admins may then delete their own account."""
import pytest
from rest_framework.test import APIClient

from apps.buildings.models import Building, BuildingCoAdmin

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user, django_user_model):
    co = django_user_model.objects.create_user(email="co@abem.test", password="CoPass1!xx", role="admin")
    b = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    BuildingCoAdmin.objects.create(user=co, building=b)
    return b


def _transfer(user, building, target):
    return _client(user).post(f"/api/v1/buildings/{building.pk}/transfer-admin/", {"user_id": str(target.pk)}, format="json")


def test_primary_admin_hands_over_to_a_co_admin(admin_user, building):
    co = building.co_admins.get()
    assert _transfer(admin_user, building, co).status_code == 200
    building.refresh_from_db()
    assert building.admin == co
    assert list(building.co_admins.all()) == [admin_user]  # the old admin stays on as co-admin


def test_after_handover_the_old_admin_can_delete_their_account(admin_user, building):
    _transfer(admin_user, building, building.co_admins.get())
    resp = _client(admin_user).post("/api/v1/auth/delete-account/", {"password": "AdminPass1!"}, format="json")
    assert resp.status_code == 200


def test_only_the_primary_admin_can_hand_over(building):
    co = building.co_admins.get()
    assert _transfer(co, building, co).status_code == 403


def test_target_must_be_a_co_admin_of_that_building(admin_user, building, django_user_model):
    stranger = django_user_model.objects.create_user(email="x@abem.test", password="XPass1!xxx", role="admin")
    assert _transfer(admin_user, building, stranger).status_code == 400
    building.refresh_from_db()
    assert building.admin == admin_user


def test_other_admins_cannot_touch_the_building(building, django_user_model):
    outsider = django_user_model.objects.create_user(email="o@abem.test", password="OPass1!xxx", role="admin")
    assert _transfer(outsider, building, building.co_admins.get()).status_code == 404
