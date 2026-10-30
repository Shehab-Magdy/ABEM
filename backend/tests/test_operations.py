"""Contractors and the obligations calendar: board keeps it, reminders go to the board."""
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from apps.buildings.models import Building, UserBuilding
from apps.operations.models import Contractor, Obligation
from apps.operations.services import mark_done, send_obligation_reminders

pytestmark = pytest.mark.django_db
TODAY = date(2026, 11, 10)


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


@pytest.fixture
def people(building, django_user_model):
    treasurer = django_user_model.objects.create_user(email="t@abem.test", password="TPass1!xxx", role="owner")
    resident = django_user_model.objects.create_user(email="r@abem.test", password="RPass1!xxx", role="owner")
    UserBuilding.objects.create(user=treasurer, building=building, board_role="treasurer")
    UserBuilding.objects.create(user=resident, building=building)
    return treasurer, resident


def _obligation(building, **extra):
    data = {"title": "Elevator contract renewal", "due_date": TODAY + timedelta(days=10), "repeat": "yearly", **extra}
    return Obligation.objects.create(building=building, **data)


def test_board_and_admins_keep_the_calendar_and_residents_read_it(admin_user, building, people):
    treasurer, resident = people
    payload = {"building_id": str(building.pk), "title": "Fire extinguisher check", "due_date": "2026-12-01", "repeat": "yearly"}
    assert _client(treasurer).post("/api/v1/operations/obligations/", payload, format="json").status_code == 201
    assert _client(admin_user).post("/api/v1/operations/obligations/", {**payload, "title": "Tank cleaning"}, format="json").status_code == 201
    assert _client(resident).post("/api/v1/operations/obligations/", payload, format="json").status_code == 403
    titles = [o["title"] for o in _client(resident).get("/api/v1/operations/obligations/").data["results"]]
    assert sorted(titles) == ["Fire extinguisher check", "Tank cleaning"]


def test_contractor_directory_is_private_to_the_building(admin_user, building, people, django_user_model):
    Contractor.objects.create(building=building, name="Ahmed", trade="Elevators", phone="0100")
    assert [c["name"] for c in _client(people[1]).get("/api/v1/operations/contractors/").data["results"]] == ["Ahmed"]
    stranger = django_user_model.objects.create_user(email="s@abem.test", password="SPass1!xxx", role="owner")
    assert _client(stranger).get("/api/v1/operations/contractors/").data["results"] == []
    other_admin = django_user_model.objects.create_user(email="oa@abem.test", password="OPass1!xxx", role="admin")
    assert _client(other_admin).get("/api/v1/operations/contractors/").data["results"] == []


def test_a_contractor_from_another_building_cannot_be_attached(admin_user, building, django_user_model):
    other = Building.objects.create(name="Other", address="9 Elm", admin=admin_user)
    foreign = Contractor.objects.create(building=other, name="Elsewhere")
    resp = _client(admin_user).post("/api/v1/operations/obligations/", {
        "building_id": str(building.pk), "title": "X", "due_date": "2026-12-01", "contractor_id": str(foreign.pk)}, format="json")
    assert resp.status_code == 400


def test_marking_a_repeating_obligation_done_moves_it_forward(building):
    ob = _obligation(building, due_date=date(2026, 11, 5), repeat="monthly")
    mark_done(ob, TODAY)
    ob.refresh_from_db()
    assert ob.last_done_on == TODAY and ob.due_date == date(2026, 12, 5) and ob.is_active


def test_a_long_overdue_repeat_skips_the_missed_periods(building):
    ob = _obligation(building, due_date=date(2026, 1, 15), repeat="quarterly")
    mark_done(ob, TODAY)
    ob.refresh_from_db()
    assert ob.due_date == date(2027, 1, 15)


def test_a_one_off_obligation_is_finished_once_done(admin_user, building):
    ob = _obligation(building, repeat="none")
    resp = _client(admin_user).post(f"/api/v1/operations/obligations/{ob.pk}/done/")
    assert resp.status_code == 200 and resp.data["is_active"] is False


def test_residents_cannot_mark_things_done(building, people):
    ob = _obligation(building)
    assert _client(people[1]).post(f"/api/v1/operations/obligations/{ob.pk}/done/").status_code == 403


def test_reminders_reach_the_admin_and_board_but_not_residents(admin_user, building, people):
    treasurer, resident = people
    _obligation(building)                                         # due in 10 days, reminded from 14 days
    assert send_obligation_reminders(TODAY) == 1
    assert admin_user.notifications.count() == 1 and treasurer.notifications.count() == 1
    assert resident.notifications.count() == 0


def test_reminders_are_weekly_and_only_when_close(building):
    _obligation(building, due_date=TODAY + timedelta(days=30))
    assert send_obligation_reminders(TODAY) == 0                  # too early
    ob = _obligation(building)
    assert send_obligation_reminders(TODAY) == 1
    assert send_obligation_reminders(TODAY + timedelta(days=3)) == 0
    assert send_obligation_reminders(TODAY + timedelta(days=7)) == 1
    ob.refresh_from_db()
    assert ob.last_reminded_on == TODAY + timedelta(days=7)


def test_overdue_and_finished_obligations(building):
    _obligation(building, due_date=TODAY - timedelta(days=3))
    _obligation(building, title="Done already", is_active=False)
    assert send_obligation_reminders(TODAY) == 1


def test_contract_renewal_reminder_30_days_before_the_end(admin_user, building):
    Contractor.objects.create(building=building, name="Ahmed", trade="Elevators", contract_end=TODAY + timedelta(days=20))
    Contractor.objects.create(building=building, name="Far away", contract_end=TODAY + timedelta(days=90))
    assert send_obligation_reminders(TODAY) == 1
    assert "Ahmed" in admin_user.notifications.get().body
