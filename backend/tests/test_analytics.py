"""Platform KPIs: only platform owners see them, and the numbers follow the data."""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db
URL = "/api/v1/analytics/platform/"


def _get(user):
    client = APIClient()
    client.force_authenticate(user)
    return client.get(URL)


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(
        email="root@abem.test", password="Pass1234!x", first_name="Root", last_name="Owner"
    )


def test_only_superusers_can_read(admin_user, owner_user, superuser):
    assert _get(admin_user).status_code == 403
    assert _get(owner_user).status_code == 403
    assert APIClient().get(URL).status_code == 401
    assert _get(superuser).status_code == 200


def test_numbers_follow_the_data(admin_user, superuser):
    busy = Building.objects.create(name="Busy", address="1 St", admin=admin_user)
    Building.objects.create(name="Empty", address="2 St", admin=admin_user)
    unit = Apartment.objects.create(building=busy, unit_number="1")
    Payment.objects.create(
        apartment=unit, amount_paid=Decimal("10.00"), payment_date=date.today(), recorded_by=admin_user
    )

    data = _get(superuser).data
    assert data["totals"]["buildings"] == 2 and data["totals"]["units"] == 1
    assert data["last_30_days"]["payments_recorded"] == 1
    assert data["last_30_days"]["active_buildings"] == 1
    assert data["activation"] == {"with_units": 1, "with_activity": 1}
    health = {b["name"]: b["health"] for b in data["buildings"]}
    assert health == {"Busy": "active", "Empty": "new"}
    assert data["signups_by_month"]
