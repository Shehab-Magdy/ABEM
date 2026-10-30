"""InstaPay display-and-confirm: residents report a transfer, admins confirm it."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def unit(admin_user, owner_user):
    building = Building.objects.create(
        name="Tower", address="1 Nile St", admin=admin_user, instapay_address="tower@instapay"
    )
    UserBuilding.objects.create(user=owner_user, building=building)
    apt = Apartment.objects.create(building=building, unit_number="1", owner=owner_user, balance=Decimal("300.00"))
    apt.owners.add(owner_user)
    return apt


@pytest.fixture
def resident(owner_user):
    # own client: the shared owner_client/admin_client fixtures reuse one APIClient
    client = APIClient()
    client.force_authenticate(owner_user)
    return client


def _claim(client, unit, amount="200.00"):
    return client.post(
        "/api/v1/payments/claims/",
        {"apartment_id": str(unit.pk), "amount": amount, "reference": "IP-123"},
        format="json",
    )


def test_resident_reports_a_transfer_and_admin_confirms_it(resident, admin_client, unit):
    resp = _claim(resident, unit)
    assert resp.status_code == 201 and resp.data["status"] == "pending"
    unit.refresh_from_db()
    assert unit.balance == Decimal("300.00")  # nothing changes until the admin confirms

    done = admin_client.post(f"/api/v1/payments/claims/{resp.data['id']}/confirm/")
    assert done.status_code == 200 and done.data["status"] == "confirmed"
    unit.refresh_from_db()
    assert unit.balance == Decimal("100.00")
    payment = Payment.objects.get(apartment=unit)
    assert payment.payment_method == "instapay" and payment.amount_paid == Decimal("200.00")

    # confirming twice must not deduct twice
    assert admin_client.post(f"/api/v1/payments/claims/{resp.data['id']}/confirm/").status_code == 409


def test_rejected_claim_changes_no_balance(resident, admin_client, unit):
    claim_id = _claim(resident, unit).data["id"]
    assert admin_client.post(f"/api/v1/payments/claims/{claim_id}/reject/").status_code == 200
    unit.refresh_from_db()
    assert unit.balance == Decimal("300.00") and not Payment.objects.exists()


def test_only_a_resident_of_the_unit_can_claim(admin_user, unit, django_user_model):
    stranger = django_user_model.objects.create_user(email="s@abem.test", password="Pass1234!x", role="owner")
    client = APIClient()
    client.force_authenticate(stranger)
    assert _claim(client, unit).status_code == 403


def test_residents_cannot_confirm_their_own_claim(resident, unit):
    claim_id = _claim(resident, unit).data["id"]
    assert resident.post(f"/api/v1/payments/claims/{claim_id}/confirm/").status_code == 403


def test_other_admins_cannot_see_or_confirm_the_claim(resident, unit, django_user_model):
    claim_id = _claim(resident, unit).data["id"]
    other = django_user_model.objects.create_user(email="b@abem.test", password="Pass1234!x", role="admin")
    client = APIClient()
    client.force_authenticate(other)
    assert client.get("/api/v1/payments/claims/").data["results"] == []
    assert client.post(f"/api/v1/payments/claims/{claim_id}/confirm/").status_code == 404
