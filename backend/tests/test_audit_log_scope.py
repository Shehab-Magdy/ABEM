"""The audit list shows rows about the admin's own buildings, never another building's, and stays fast."""

import uuid

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.audit.models import AuditLog
from apps.buildings.models import Building, UserBuilding

pytestmark = pytest.mark.django_db


def _get(user, url="/api/v1/audit/"):
    client = APIClient()
    client.force_authenticate(user)
    return client.get(url)


def test_audit_list_excludes_other_buildings_even_for_a_shared_member(admin_user, owner_user, django_user_model):
    mine = Building.objects.create(name="Mine", address="1 St", admin=admin_user)
    other_admin = django_user_model.objects.create_user(email="o@x.com", password="Passw0rd!x", role="admin")
    theirs = Building.objects.create(name="Theirs", address="2 St", admin=other_admin)
    UserBuilding.objects.create(user=owner_user, building=mine)
    UserBuilding.objects.create(user=owner_user, building=theirs)  # the shared person lives in both
    unit_mine = Apartment.objects.create(building=mine, unit_number="1")
    unit_theirs = Apartment.objects.create(building=theirs, unit_number="1")
    AuditLog.objects.create(user=owner_user, action="update", entity="apartment", entity_id=unit_mine.pk)
    AuditLog.objects.create(user=owner_user, action="update", entity="apartment", entity_id=unit_theirs.pk)
    AuditLog.objects.create(user=other_admin, action="update", entity="building", entity_id=theirs.pk)

    res = _get(admin_user)
    ids = {r["entity_id"] for r in res.data["results"]}

    assert res.status_code == 200
    assert str(unit_mine.pk) in ids
    assert str(unit_theirs.pk) not in ids
    assert str(theirs.pk) not in ids


def test_audit_list_uses_a_constant_number_of_queries(admin_user):
    building = Building.objects.create(name="Mine", address="1 St", admin=admin_user)
    for _ in range(25):
        AuditLog.objects.create(user=admin_user, action="update", entity="building", entity_id=building.pk)
    AuditLog.objects.create(user=None, action="x", entity="y", entity_id=uuid.uuid4())

    with CaptureQueriesContext(connection) as q:
        res = _get(admin_user, "/api/v1/audit/?page=1&page_size=10")

    assert res.status_code == 200
    assert len(res.data["results"]) == 10
    assert len(q) <= 6
