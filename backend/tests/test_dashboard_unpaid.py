from decimal import Decimal

import pytest

from apps.apartments.models import Apartment
from apps.buildings.models import Building

pytestmark = pytest.mark.django_db


def test_unpaid_units_include_the_owner_phone_for_whatsapp_reminders(admin_client, admin_user, owner_user):
    owner_user.phone = "01012345678"
    owner_user.save()
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    Apartment.objects.create(building=building, unit_number="2", owner=owner_user, balance=Decimal("250.00"))

    rows = admin_client.get("/api/v1/dashboard/admin/").data["unpaid_units"]
    assert rows[0]["owner_phone"] == "01012345678" and rows[0]["unit_number"] == "2"
