"""Regression: custom actions declared admin-only permissions that the viewset silently ignored."""
import pytest
from rest_framework.test import APIClient

from apps.buildings.models import Building, UserBuilding

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_a_resident_member_cannot_read_or_change_the_subscription_plan(admin_user, owner_user):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    UserBuilding.objects.create(user=owner_user, building=building)
    url = f"/api/v1/buildings/{building.pk}/subscription/"
    assert _client(owner_user).post(url, {"amount": "999"}, format="json").status_code == 403
    assert _client(owner_user).get(url).status_code == 403
    assert _client(admin_user).post(url, {"amount": "150"}, format="json").status_code == 200   # admins still can


def test_member_read_views_still_work_for_residents(admin_user, owner_user):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    UserBuilding.objects.create(user=owner_user, building=building)
    for path in ("treasury", "statement", "board"):
        assert _client(owner_user).get(f"/api/v1/buildings/{building.pk}/{path}/").status_code == 200, path
