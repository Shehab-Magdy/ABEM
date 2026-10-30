"""Board titles: one holder each, assigned by admins; the treasurer confirms InstaPay transfers."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


@pytest.fixture
def members(building, django_user_model):
    made = []
    for n in range(1, 4):
        u = django_user_model.objects.create_user(email=f"m{n}@abem.test", password="MPass1!xxx", role="owner", first_name=f"M{n}")
        UserBuilding.objects.create(user=u, building=building)
        made.append(u)
    return made


def _assign(admin_user, building, user, role):
    return _client(admin_user).post(f"/api/v1/buildings/{building.pk}/board/", {"user_id": str(user.pk), "role": role}, format="json")


def test_admin_assigns_titles_and_members_can_see_them(admin_user, building, members):
    assert _assign(admin_user, building, members[0], "chair").status_code == 200
    _assign(admin_user, building, members[1], "treasurer")
    board = {b["role"]: b for b in _client(members[2]).get(f"/api/v1/buildings/{building.pk}/board/").data["board"]}
    assert board["chair"]["user_id"] == str(members[0].pk) and board["treasurer"]["user_id"] == str(members[1].pk)
    assert board["secretary"]["user_id"] is None
    assert "candidates" not in _client(members[2]).get(f"/api/v1/buildings/{building.pk}/board/").data


def test_a_title_has_one_holder(admin_user, building, members):
    _assign(admin_user, building, members[0], "chair")
    _assign(admin_user, building, members[1], "chair")
    assert UserBuilding.objects.get(user=members[0], building=building).board_role == ""
    assert UserBuilding.objects.get(user=members[1], building=building).board_role == "chair"
    _assign(admin_user, building, members[1], "")
    assert UserBuilding.objects.get(user=members[1], building=building).board_role == ""


def test_only_building_admins_assign_and_only_to_members(admin_user, building, members, django_user_model):
    assert _assign(members[0], building, members[1], "chair").status_code == 403
    assert _assign(admin_user, building, members[0], "boss").status_code == 400
    stranger = django_user_model.objects.create_user(email="s@abem.test", password="SPass1!xxx", role="owner")
    assert _assign(admin_user, building, stranger, "chair").status_code == 400
    outsider = django_user_model.objects.create_user(email="x@abem.test", password="XPass1!xxx", role="admin")
    assert _assign(outsider, building, members[0], "chair").status_code == 404


def test_the_treasurer_confirms_instapay_transfers(admin_user, building, members):
    payer, treasurer, other = members
    unit = Apartment.objects.create(building=building, unit_number="1", owner=payer, balance=Decimal("300.00"))
    unit.owners.add(payer)
    _assign(admin_user, building, treasurer, "treasurer")

    claim = _client(payer).post("/api/v1/payments/claims/", {"apartment_id": str(unit.pk), "amount": "100.00"}, format="json").data
    assert [c["id"] for c in _client(treasurer).get("/api/v1/payments/claims/").data["results"]] == [claim["id"]]
    assert _client(other).get("/api/v1/payments/claims/").data["results"] == []           # not a party, not treasurer
    assert _client(other).post(f"/api/v1/payments/claims/{claim['id']}/confirm/").status_code == 404

    assert _client(treasurer).post(f"/api/v1/payments/claims/{claim['id']}/confirm/").status_code == 200
    unit.refresh_from_db()
    assert unit.balance == Decimal("200.00")


def test_a_resident_cannot_confirm_their_own_transfer(admin_user, building, members):
    payer = members[0]
    unit = Apartment.objects.create(building=building, unit_number="1", owner=payer, balance=Decimal("300.00"))
    unit.owners.add(payer)
    claim = _client(payer).post("/api/v1/payments/claims/", {"apartment_id": str(unit.pk), "amount": "100.00"}, format="json").data
    assert _client(payer).post(f"/api/v1/payments/claims/{claim['id']}/confirm/").status_code == 403
    assert _client(payer).post(f"/api/v1/payments/claims/{claim['id']}/reject/").status_code == 403


def test_a_treasurer_of_another_building_has_no_powers_here(admin_user, building, members, django_user_model):
    other_admin = django_user_model.objects.create_user(email="oa@abem.test", password="OAPass1!xx", role="admin")
    other_building = Building.objects.create(name="Other", address="9 Elm", admin=other_admin)
    UserBuilding.objects.create(user=members[1], building=other_building, board_role="treasurer")
    payer = members[0]
    unit = Apartment.objects.create(building=building, unit_number="1", owner=payer, balance=Decimal("300.00"))
    unit.owners.add(payer)
    claim = _client(payer).post("/api/v1/payments/claims/", {"apartment_id": str(unit.pk), "amount": "100.00"}, format="json").data
    assert _client(members[1]).post(f"/api/v1/payments/claims/{claim['id']}/confirm/").status_code == 404
