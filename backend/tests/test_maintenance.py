import pytest
from rest_framework.test import APIClient

from apps.buildings.models import Building, UserBuilding

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user, owner_user):
    b = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    UserBuilding.objects.create(user=owner_user, building=b)
    return b


def _report(client, building, category="elevator"):
    return client.post(
        "/api/v1/maintenance/",
        {"building_id": str(building.pk), "category": category, "description": "Stuck on 3rd floor"},
        format="json",
    )


def test_resident_files_a_report_and_the_admin_sees_it(owner_user, admin_user, building):
    resp = _report(_client(owner_user), building)
    assert resp.status_code == 201 and resp.data["status"] == "open"
    listed = _client(admin_user).get("/api/v1/maintenance/").data["results"]
    assert [r["id"] for r in listed] == [resp.data["id"]]


def test_admin_updates_status_but_residents_cannot(owner_user, admin_user, building):
    report_id = _report(_client(owner_user), building).data["id"]
    assert _client(owner_user).patch(f"/api/v1/maintenance/{report_id}/", {"status": "done"}, format="json").status_code == 403
    resp = _client(admin_user).patch(f"/api/v1/maintenance/{report_id}/", {"status": "in_progress"}, format="json")
    assert resp.status_code == 200 and resp.data["status"] == "in_progress"


def test_only_members_can_report_for_a_building(building, django_user_model):
    stranger = django_user_model.objects.create_user(email="s@abem.test", password="Pass1234!x", role="owner")
    assert _report(_client(stranger), building).status_code == 403


def test_other_admins_do_not_see_the_report(owner_user, building, django_user_model):
    _report(_client(owner_user), building)
    other = django_user_model.objects.create_user(email="b@abem.test", password="Pass1234!x", role="admin")
    assert _client(other).get("/api/v1/maintenance/").data["results"] == []
