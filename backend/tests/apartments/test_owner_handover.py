"""R-25: changing a unit's owner revokes the previous owner's access, is audited and is limited to building members."""

from decimal import Decimal

import pytest
from apps.apartments.models import Apartment
from apps.audit.models import AuditLog
from apps.buildings.models import Building, UserBuilding
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(admin_user, django_user_model):
    building = Building.objects.create(name="B", address="1 A St", admin=admin_user)
    old = django_user_model.objects.create_user(email="old@abem.test", password="Passw0rd!x", role="owner")
    new = django_user_model.objects.create_user(email="new@abem.test", password="Passw0rd!x", role="owner")
    stranger = django_user_model.objects.create_user(email="x@abem.test", password="Passw0rd!x", role="owner")
    unit = Apartment.objects.create(building=building, unit_number="1", owner=old, balance=Decimal("250.00"))
    unit.owners.add(old)
    UserBuilding.objects.create(user=old, building=building)
    UserBuilding.objects.create(user=new, building=building)
    return {"building": building, "unit": unit, "old": old, "new": new, "stranger": stranger}


def _patch(client, unit, user):
    return client.patch(f"/api/v1/apartments/{unit.pk}/", {"owner_id": str(user.pk)}, format="json")


def test_previous_owner_loses_access(admin_client, setup):
    resp = _patch(admin_client, setup["unit"], setup["new"])
    assert resp.status_code == 200, resp.data
    unit, b = setup["unit"], setup["building"]
    unit.refresh_from_db()
    assert unit.owner_id == setup["new"].pk
    assert not unit.owners.filter(pk=setup["old"].pk).exists()
    assert not UserBuilding.objects.filter(user=setup["old"], building=b).exists()
    assert UserBuilding.objects.filter(user=setup["new"], building=b).exists()


def test_previous_owner_keeps_access_with_another_unit(admin_client, setup):
    other = Apartment.objects.create(building=setup["building"], unit_number="2", owner=setup["old"])
    other.owners.add(setup["old"])
    assert _patch(admin_client, setup["unit"], setup["new"]).status_code == 200
    assert UserBuilding.objects.filter(user=setup["old"], building=setup["building"]).exists()


def test_handover_is_audited_with_balance_and_admin_notified(admin_client, admin_user, setup):
    _patch(admin_client, setup["unit"], setup["new"])
    entry = AuditLog.objects.get(action="owner_changed", entity_id=setup["unit"].pk)
    assert entry.changes["balance"] == "250.00"
    assert entry.changes["before"] == str(setup["old"].pk)
    assert entry.changes["after"] == str(setup["new"].pk)
    assert Notification.objects.filter(user=admin_user, metadata__apartment_id=str(setup["unit"].pk)).exists()


def test_owner_must_already_be_in_the_building(admin_client, setup):
    resp = _patch(admin_client, setup["unit"], setup["stranger"])
    assert resp.status_code == 400
    setup["unit"].refresh_from_db()
    assert setup["unit"].owner_id == setup["old"].pk


def test_stranger_cannot_be_assigned_on_create(admin_client, setup):
    resp = admin_client.post(
        "/api/v1/apartments/",
        {
            "building_id": str(setup["building"].pk),
            "unit_number": "7",
            "floor": 0,
            "type": "apartment",
            "owner_id": str(setup["stranger"].pk),
        },
        format="json",
    )
    assert resp.status_code == 400


def test_handover_reports_removed_board_role(admin_client, admin_user, setup):
    UserBuilding.objects.filter(user=setup["old"], building=setup["building"]).update(board_role="treasurer")
    _patch(admin_client, setup["unit"], setup["new"])
    entry = AuditLog.objects.get(action="owner_changed", entity_id=setup["unit"].pk)
    assert entry.changes["board_role_removed"] == "treasurer"
    note = Notification.objects.get(user=admin_user, metadata__apartment_id=str(setup["unit"].pk))
    assert "treasurer" in note.body.lower()


def test_handover_without_board_role_has_no_board_note(admin_client, admin_user, setup):
    _patch(admin_client, setup["unit"], setup["new"])
    entry = AuditLog.objects.get(action="owner_changed", entity_id=setup["unit"].pk)
    assert "board_role_removed" not in entry.changes
