"""Polls: one vote per unit, owners only, results after closing, quorum and majority."""
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding
from apps.governance.models import Poll

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


@pytest.fixture
def residents(building, django_user_model):
    """Four owned units (owners o1..o4) and a renter living in unit 1."""
    users = []
    for n in range(1, 5):
        u = django_user_model.objects.create_user(email=f"o{n}@abem.test", password="OPass1!xxx", role="owner")
        apt = Apartment.objects.create(building=building, unit_number=str(n), owner=u)
        apt.owners.add(u)
        UserBuilding.objects.create(user=u, building=building)
        users.append((u, apt))
    renter = django_user_model.objects.create_user(email="r@abem.test", password="RPass1!xxx", role="renter")
    users[0][1].owners.add(renter)
    UserBuilding.objects.create(user=renter, building=building)
    return {"owners": users, "renter": renter}


def _create(admin_user, building, **extra):
    payload = {
        "building_id": str(building.pk), "title": "Replace the elevator?", "options": ["Yes", "No"],
        "closes_at": (timezone.now() + timedelta(days=3)).isoformat(), **extra,
    }
    return _client(admin_user).post("/api/v1/governance/polls/", payload, format="json")


def _vote(user, poll_id, apartment, option_id):
    return _client(user).post(
        f"/api/v1/governance/polls/{poll_id}/vote/",
        {"apartment_id": str(apartment.pk), "option_id": option_id}, format="json",
    )


def _option(poll_data, text):
    return next(o["id"] for o in poll_data["options"] if o["text"] == text)


def test_admin_creates_a_poll_and_residents_are_notified(admin_user, building, residents):
    resp = _create(admin_user, building)
    assert resp.status_code == 201 and [o["text"] for o in resp.data["options"]] == ["Yes", "No"]
    assert residents["owners"][0][0].notifications.count() == 1


def test_validation_of_new_polls(admin_user, building):
    assert _create(admin_user, building, options=["Only one"]).status_code == 400
    past = (timezone.now() - timedelta(days=1)).isoformat()
    assert _create(admin_user, building, closes_at=past).status_code == 400


def test_other_admins_and_residents_cannot_create_polls(building, residents, django_user_model):
    outsider = django_user_model.objects.create_user(email="x@abem.test", password="XPass1!xxx", role="admin")
    assert _create(outsider, building).status_code == 403
    assert _create(residents["owners"][0][0], building).status_code == 403


def test_one_vote_per_unit_and_it_can_be_changed(admin_user, building, residents):
    poll = _create(admin_user, building).data
    owner, apt = residents["owners"][0]
    assert _vote(owner, poll["id"], apt, _option(poll, "Yes")).status_code == 200
    assert _vote(owner, poll["id"], apt, _option(poll, "No")).status_code == 200  # changed their mind
    results = _client(admin_user).get(f"/api/v1/governance/polls/{poll['id']}/").data["results"]
    assert results["votes_cast"] == 1
    assert {o["text"]: o["votes"] for o in results["options"]} == {"Yes": 0, "No": 1}


def test_co_owners_share_a_units_single_vote(admin_user, building, residents, django_user_model):
    poll = _create(admin_user, building).data
    owner, apt = residents["owners"][0]
    spouse = django_user_model.objects.create_user(email="s@abem.test", password="SPass1!xxx", role="owner")
    apt.owners.add(spouse)
    UserBuilding.objects.create(user=spouse, building=building)
    _vote(owner, poll["id"], apt, _option(poll, "Yes"))
    _vote(spouse, poll["id"], apt, _option(poll, "No"))
    results = _client(admin_user).get(f"/api/v1/governance/polls/{poll['id']}/").data["results"]
    assert results["votes_cast"] == 1


def test_renters_and_other_units_owners_cannot_vote(admin_user, building, residents):
    poll = _create(admin_user, building).data
    (owner1, apt1), (owner2, apt2) = residents["owners"][0], residents["owners"][1]
    assert _vote(residents["renter"], poll["id"], apt1, _option(poll, "Yes")).status_code == 403
    assert _vote(owner2, poll["id"], apt1, _option(poll, "Yes")).status_code == 403


def test_residents_see_results_only_after_the_vote_closes(admin_user, building, residents):
    poll = _create(admin_user, building).data
    owner, apt = residents["owners"][0]
    _vote(owner, poll["id"], apt, _option(poll, "Yes"))
    during = _client(owner).get(f"/api/v1/governance/polls/{poll['id']}/").data
    assert "results" not in during and during["my_votes"][0]["apartment_id"] == str(apt.pk)

    assert _client(admin_user).post(f"/api/v1/governance/polls/{poll['id']}/close/").status_code == 200
    after = _client(owner).get(f"/api/v1/governance/polls/{poll['id']}/").data
    assert after["results"]["votes_cast"] == 1
    assert _vote(owner, poll["id"], apt, _option(poll, "No")).status_code == 409  # closed


def _close(admin_user, poll_id):
    return _client(admin_user).post(f"/api/v1/governance/polls/{poll_id}/close/")


def test_simple_majority_passes(admin_user, building, residents):
    poll = _create(admin_user, building).data
    for (owner, apt), choice in zip(residents["owners"], ["Yes", "Yes", "Yes", "No"]):
        _vote(owner, poll["id"], apt, _option(poll, choice))
    results = _close(admin_user, poll["id"]).data["results"]
    assert results["outcome"] == "passed" and results["winning_option_id"] == _option(poll, "Yes")
    assert results["turnout_percent"] == 100


def test_a_tie_has_no_majority(admin_user, building, residents):
    poll = _create(admin_user, building).data
    for (owner, apt), choice in zip(residents["owners"], ["Yes", "Yes", "No", "No"]):
        _vote(owner, poll["id"], apt, _option(poll, choice))
    assert _close(admin_user, poll["id"]).data["results"]["outcome"] == "no_majority"


def test_two_thirds_rule(admin_user, building, residents):
    poll = _create(admin_user, building, majority="two_thirds").data
    for (owner, apt), choice in zip(residents["owners"], ["Yes", "Yes", "Yes", "No"]):  # 3 of 4 = 75%
        _vote(owner, poll["id"], apt, _option(poll, choice))
    assert _close(admin_user, poll["id"]).data["results"]["outcome"] == "passed"

    poll2 = _create(admin_user, building, majority="two_thirds", title="Second").data
    for (owner, apt), choice in zip(residents["owners"], ["Yes", "Yes", "No", "No"]):  # 50%
        _vote(owner, poll2["id"], apt, _option(poll2, choice))
    assert _close(admin_user, poll2["id"]).data["results"]["outcome"] == "no_majority"


def test_quorum_must_be_reached(admin_user, building, residents):
    poll = _create(admin_user, building, quorum_percent=75).data
    for (owner, apt) in residents["owners"][:2]:  # 2 of 4 units = 50% turnout
        _vote(owner, poll["id"], apt, _option(poll, "Yes"))
    results = _close(admin_user, poll["id"]).data["results"]
    assert results["turnout_percent"] == 50 and not results["quorum_met"] and results["outcome"] == "no_quorum"


def test_renters_do_not_count_toward_eligible_units(admin_user, building, residents):
    results = _client(admin_user).get(f"/api/v1/governance/polls/{_create(admin_user, building).data['id']}/").data["results"]
    assert results["eligible_units"] == 4


def test_strangers_do_not_see_other_buildings_polls(admin_user, building, residents, django_user_model):
    poll = _create(admin_user, building).data
    stranger = django_user_model.objects.create_user(email="z@abem.test", password="ZPass1!xxx", role="owner")
    assert _client(stranger).get(f"/api/v1/governance/polls/{poll['id']}/").status_code == 404
    assert _client(stranger).get("/api/v1/governance/polls/").data["results"] == []
