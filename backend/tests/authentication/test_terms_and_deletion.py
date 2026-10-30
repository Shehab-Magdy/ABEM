"""Terms acceptance at sign-up and account deletion."""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, BuildingCoAdmin, UserBuilding
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db

SIGNUP = {
    "email": "new@3mara.test", "first_name": "منى", "last_name": "السكن", "role": "owner",
    "password": "Strong1!pass", "confirm_password": "Strong1!pass",
}


def test_signup_requires_accepting_the_terms(api_client):
    assert api_client.post("/api/v1/auth/self-register/", SIGNUP, format="json").status_code == 400
    assert api_client.post("/api/v1/auth/self-register/", {**SIGNUP, "accept_terms": False}, format="json").status_code == 400


def test_signup_records_when_the_terms_were_accepted(api_client, django_user_model):
    resp = api_client.post("/api/v1/auth/self-register/", {**SIGNUP, "accept_terms": True}, format="json")
    assert resp.status_code == 201
    assert django_user_model.objects.get(email="new@3mara.test").terms_accepted_at is not None


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_deleting_an_account_erases_the_person_but_keeps_the_books(admin_user, owner_user):
    owner_user.phone = "01012345678"
    owner_user.save()
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    unit = Apartment.objects.create(building=building, unit_number="1", owner=owner_user)
    unit.owners.add(owner_user)
    UserBuilding.objects.create(user=owner_user, building=building)
    payment = Payment.objects.create(
        apartment=unit, amount_paid=Decimal("50.00"), payment_date=date.today(), recorded_by=admin_user
    )

    resp = _client(owner_user).post("/api/v1/auth/delete-account/", {"password": "OwnerPass1!"}, format="json")
    assert resp.status_code == 200

    owner_user.refresh_from_db()
    assert not owner_user.is_active and owner_user.phone == "" and owner_user.first_name == ""
    assert owner_user.email.endswith("@deleted.invalid") and not owner_user.has_usable_password()
    unit.refresh_from_db()
    assert unit.owner is None and not unit.owners.exists()
    assert not UserBuilding.objects.filter(user=owner_user).exists()
    assert Payment.objects.filter(pk=payment.pk).exists()  # financial record stays


def test_wrong_password_does_not_delete(owner_user):
    resp = _client(owner_user).post("/api/v1/auth/delete-account/", {"password": "nope"}, format="json")
    assert resp.status_code == 400
    owner_user.refresh_from_db()
    assert owner_user.is_active


def test_primary_admin_must_hand_over_first(admin_user, django_user_model):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    resp = _client(admin_user).post("/api/v1/auth/delete-account/", {"password": "AdminPass1!"}, format="json")
    assert resp.status_code == 409
    admin_user.refresh_from_db()
    assert admin_user.is_active

    # a co-admin may leave without blocking anyone
    co_admin = django_user_model.objects.create_user(email="co@abem.test", password="CoPass1!xx", role="admin")
    BuildingCoAdmin.objects.create(user=co_admin, building=building)
    assert _client(co_admin).post("/api/v1/auth/delete-account/", {"password": "CoPass1!xx"}, format="json").status_code == 200
    assert not BuildingCoAdmin.objects.filter(user=co_admin).exists()


def test_a_deleted_account_cannot_sign_in(owner_user, api_client):
    _client(owner_user).post("/api/v1/auth/delete-account/", {"password": "OwnerPass1!"}, format="json")
    resp = api_client.post("/api/v1/auth/login/", {"email": "owner@abem.test", "password": "OwnerPass1!"}, format="json")
    assert resp.status_code in (400, 401, 403)
