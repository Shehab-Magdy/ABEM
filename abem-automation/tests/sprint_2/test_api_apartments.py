"""
Sprint 2 — Apartments API tests.

Covers apartment-related API test cases from the QA Strategy:
  TC-S2-API-017 to TC-S2-API-027   Apartment CRUD & permissions
  TC-S2-API-029 to TC-S2-API-030   Apartment filter & search
  TC-S2-API-035                    Balance initialisation
  TC-S2-API-019                    Nested /buildings/{id}/apartments/

Markers: sprint_2, api
"""
import pytest

from api.apartment_api import ApartmentAPI
from api.building_api import BuildingAPI
from utils.test_data import ApartmentFactory, BuildingFactory

pytestmark = [pytest.mark.sprint_2, pytest.mark.api]


# ── Apartment CRUD (TC-S2-API-017 to TC-S2-API-021) ──────────────────────────

@pytest.mark.positive
class TestApartmentCRUD:
    """TC-S2-API-017 to TC-S2-API-021: Basic create/read/update/delete."""

    def test_admin_create_apartment_returns_201(self, admin_api, temp_building):
        """TC-S2-API-017: Admin POST /apartments/ with valid data → 201."""
        apartment_api = ApartmentAPI(admin_api)
        data = ApartmentFactory.valid(
            building_id=temp_building["id"],
            num_floors=temp_building["num_floors"],
        )
        resp = apartment_api.create(**data)
        assert resp.status_code == 201, resp.text

        # Cleanup
        apartment_api.delete(resp.json()["id"])

    def test_create_response_contains_required_fields(self, admin_api, temp_building):
        """TC-S2-API-018: Response contains id, floor, type, building_id."""
        apartment_api = ApartmentAPI(admin_api)
        data = ApartmentFactory.valid(
            building_id=temp_building["id"],
            num_floors=temp_building["num_floors"],
        )
        resp = apartment_api.create(**data)
        assert resp.status_code == 201, resp.text
        body = resp.json()

        for field in ("id", "floor", "type", "building_id"):
            assert field in body, f"Missing field '{field}' in create response"

        # Cleanup
        apartment_api.delete(body["id"])

    def test_admin_list_apartments_in_building(
        self, admin_api, temp_building, create_temp_apartment
    ):
        """TC-S2-API-019: GET /buildings/{id}/apartments/ lists all apartments."""
        apt = create_temp_apartment(
            building_id=temp_building["id"],
            num_floors=temp_building["num_floors"],
        )
        building_api = BuildingAPI(admin_api)
        resp = building_api.list_apartments(temp_building["id"])
        assert resp.status_code == 200, resp.text
        results = resp.json().get("results", resp.json())
        ids = [a["id"] for a in results]
        assert apt["id"] in ids, "Created apartment must appear in building's apartment list"

    def test_admin_update_apartment(self, admin_api, temp_apartment):
        """TC-S2-API-020: Admin PATCH /apartments/{id}/ updates floor and size."""
        apartment_api = ApartmentAPI(admin_api)
        new_floor = min(temp_apartment["floor"], 1)
        resp = apartment_api.update(
            temp_apartment["id"],
            floor=new_floor,
            size_sqm=99.99,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert float(body["size_sqm"]) == 99.99

    def test_admin_delete_apartment(self, admin_api, create_temp_building, create_temp_apartment):
        """TC-S2-API-021: Admin DELETE /apartments/{id}/ removes the apartment."""
        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
        )
        apartment_api = ApartmentAPI(admin_api)
        resp = apartment_api.delete(apt["id"])
        assert resp.status_code in (200, 204), resp.text

        # Confirm it's gone
        get_resp = apartment_api.get(apt["id"])
        assert get_resp.status_code == 404, (
            f"Deleted apartment must return 404 (got {get_resp.status_code})"
        )


# ── Apartment Validation — Negatives (TC-S2-API-022 to TC-S2-API-023) ─────────

@pytest.mark.negative
class TestApartmentValidation:
    """TC-S2-API-022 to TC-S2-API-023: Validation failures → 400."""

    def test_invalid_unit_type_returns_400(self, admin_api, temp_building):
        """TC-S2-API-022: POST with type='InvalidType' → 400."""
        apartment_api = ApartmentAPI(admin_api)
        data = ApartmentFactory.invalid_type(building_id=temp_building["id"])
        resp = apartment_api.create(**data)
        assert resp.status_code == 400, resp.text

    def test_floor_exceeds_building_floors_returns_400(self, admin_api, temp_building):
        """TC-S2-API-023: POST with floor > building.num_floors → 400."""
        apartment_api = ApartmentAPI(admin_api)
        data = ApartmentFactory.floor_exceeds_max(
            building_id=temp_building["id"],
            num_floors=temp_building["num_floors"],
        )
        resp = apartment_api.create(**data)
        assert resp.status_code == 400, resp.text


# ── Apartment Permissions & Owner Access (TC-S2-API-024 to TC-S2-API-026) ─────

@pytest.mark.positive
class TestApartmentPermissions:
    """TC-S2-API-024 to TC-S2-API-026: Owner access restrictions."""

    def test_owner_can_get_own_apartment(
        self, admin_api, owner_with_id, create_temp_building, create_temp_apartment
    ):
        """TC-S2-API-024: Owner can GET /apartments/{id}/ for their own apartment."""
        owner_client, owner_id = owner_with_id
        building = create_temp_building(num_floors=5)

        # Assign the owner to the building first
        building_api_admin = BuildingAPI(admin_api)
        building_api_admin.assign_user(building["id"], user_id=str(owner_id))

        # Create apartment and assign to the owner
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
            owner_id=str(owner_id),
        )

        apartment_api_owner = ApartmentAPI(owner_client)
        resp = apartment_api_owner.get(apt["id"])
        assert resp.status_code == 200, (
            f"Owner must be able to GET their own apartment (got {resp.status_code})"
        )
        assert resp.json()["id"] == apt["id"]

    def test_owner_cannot_get_another_apartment(
        self, admin_api, owner_api, create_temp_building, create_temp_apartment
    ):
        """TC-S2-API-025: Owner cannot GET /apartments/{id}/ for another apartment."""
        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
        )

        apartment_api_owner = ApartmentAPI(owner_api)
        resp = apartment_api_owner.get(apt["id"])
        assert resp.status_code in (403, 404), (
            f"Owner must not see apartments not assigned to them (got {resp.status_code})"
        )

    def test_admin_assign_owner_to_apartment(
        self, admin_api, owner_with_id, create_temp_building, create_temp_apartment
    ):
        """TC-S2-API-026: Admin PATCH /apartments/{id}/ with owner_id assigns owner."""
        owner_client, owner_id = owner_with_id
        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
        )

        apartment_api = ApartmentAPI(admin_api)
        resp = apartment_api.update(apt["id"], owner_id=str(owner_id))
        assert resp.status_code == 200, resp.text
        assert str(resp.json()["owner_id"]) == str(owner_id)

    def test_owner_cannot_create_apartment(self, owner_api, admin_api, temp_building):
        """Owner POST /apartments/ must return 403."""
        apartment_api = ApartmentAPI(owner_api)
        from utils.test_data import ApartmentFactory
        data = ApartmentFactory.valid(
            building_id=temp_building["id"],
            num_floors=temp_building["num_floors"],
        )
        resp = apartment_api.create(**data)
        assert resp.status_code == 403, (
            f"Owner must not create apartments (got {resp.status_code})"
        )


# ── Apartment Data Integrity (TC-S2-API-027 & TC-S2-API-035) ─────────────────

@pytest.mark.positive
class TestApartmentDataIntegrity:
    """TC-S2-API-027: Store type stored correctly. TC-S2-API-035: Balance = 0.00."""

    def test_store_type_stored_and_returned_correctly(
        self, admin_api, temp_building, create_temp_apartment
    ):
        """TC-S2-API-027: Apartment with type='store' is stored and returned as 'store'."""
        from utils.test_data import ApartmentFactory

        apartment_api = ApartmentAPI(admin_api)
        data = ApartmentFactory.store(
            building_id=temp_building["id"],
            num_floors=temp_building["num_floors"],
        )
        resp = apartment_api.create(**data)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["type"] == "store", (
            f"Expected type='store', got '{body.get('type')}'"
        )

        # Cleanup
        apartment_api.delete(body["id"])

    def test_balance_initialises_to_zero(self, admin_api, temp_building):
        """TC-S2-API-035: Newly created apartment has balance=0.00."""
        apartment_api = ApartmentAPI(admin_api)
        data = ApartmentFactory.valid(
            building_id=temp_building["id"],
            num_floors=temp_building["num_floors"],
        )
        resp = apartment_api.create(**data)
        assert resp.status_code == 201, resp.text
        balance = resp.json().get("balance", "MISSING")
        assert balance != "MISSING", "balance field must be present in response"
        assert float(balance) == 0.0, (
            f"New apartment balance must be 0.00, got {balance}"
        )

        # Cleanup
        apartment_api.delete(resp.json()["id"])


# ── Apartment Search & Filter (TC-S2-API-029 to TC-S2-API-030) ───────────────

@pytest.mark.positive
class TestApartmentFilter:
    """TC-S2-API-029 to TC-S2-API-030: Filter by type and building_id."""

    def test_filter_by_type_store(self, admin_api, temp_building, create_temp_apartment):
        """TC-S2-API-029: GET /apartments/?unit_type=store returns only stores."""
        from utils.test_data import ApartmentFactory

        apartment_api = ApartmentAPI(admin_api)
        # Create a store-type apartment
        store_data = ApartmentFactory.store(
            building_id=temp_building["id"],
            num_floors=temp_building["num_floors"],
        )
        resp = apartment_api.create(**store_data)
        assert resp.status_code == 201, resp.text
        store_id = resp.json()["id"]

        # Filter
        list_resp = apartment_api.list(unit_type="store")
        assert list_resp.status_code == 200, list_resp.text
        results = list_resp.json().get("results", list_resp.json())
        for apt in results:
            assert apt["type"] == "store", (
                f"Filter by type=store returned non-store: {apt}"
            )

        # Cleanup
        apartment_api.delete(store_id)

    def test_filter_by_building_id(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S2-API-030: GET /apartments/?building_id={id} scopes results."""
        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
        )

        apartment_api = ApartmentAPI(admin_api)
        resp = apartment_api.list(building_id=building["id"])
        assert resp.status_code == 200, resp.text
        results = resp.json().get("results", resp.json())
        ids = [a["id"] for a in results]
        assert apt["id"] in ids, "Filter by building_id must include created apartment"
        for a in results:
            assert str(a["building_id"]) == building["id"], (
                f"Apartment {a['id']} has wrong building_id: {a['building_id']}"
            )


# ── Available Apartments & Claim — sign-up wizard ─────────────────────────────

@pytest.mark.positive
class TestApartmentAvailablePositive:
    """
    GET /apartments/available/?building_id={id}
    Used in the owner sign-up wizard to list unowned (vacant) apartments.
    """

    def test_available_returns_200_with_list(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """Authenticated user gets 200 + a JSON array for a valid building."""
        building = create_temp_building(num_floors=5)
        apartment_api = ApartmentAPI(admin_api)
        resp = apartment_api.available(building["id"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list), "Available endpoint must return a JSON array"

    def test_available_includes_vacant_apartment(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """A newly created (unowned, status=vacant) apartment appears in available."""
        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
        )
        apartment_api = ApartmentAPI(admin_api)
        resp = apartment_api.available(building["id"])
        assert resp.status_code == 200, resp.text
        ids = [a["id"] for a in resp.json()]
        assert apt["id"] in ids, (
            "Unowned apartment must appear in /apartments/available/"
        )

    def test_available_excludes_owned_apartment(
        self, admin_api, owner_with_id, create_temp_building, create_temp_apartment
    ):
        """An apartment that has an owner assigned must NOT appear in available."""
        _, owner_id = owner_with_id
        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
            owner_id=str(owner_id),
        )
        apartment_api = ApartmentAPI(admin_api)
        resp = apartment_api.available(building["id"])
        assert resp.status_code == 200, resp.text
        ids = [a["id"] for a in resp.json()]
        assert apt["id"] not in ids, (
            "Owned apartment must NOT appear in /apartments/available/"
        )


@pytest.mark.negative
class TestApartmentAvailableNegative:

    def test_available_without_building_id_returns_400(self, admin_api):
        """GET /apartments/available/ without building_id param → 400."""
        resp = admin_api.get("/apartments/available/")
        assert resp.status_code == 400, (
            f"Missing building_id must return 400, got {resp.status_code}: {resp.text}"
        )

    def test_available_requires_authentication(self, unauthenticated_api):
        """Unauthenticated GET /apartments/available/ → 401."""
        resp = unauthenticated_api.get(
            "/apartments/available/", params={"building_id": "any"}
        )
        assert resp.status_code == 401, (
            f"Available must require auth (got {resp.status_code})"
        )


@pytest.mark.positive
class TestApartmentClaimPositive:
    """
    POST /apartments/{id}/claim/
    Owner self-assigns to a vacant apartment during sign-up.
    """

    def test_owner_can_claim_vacant_apartment(
        self, env_config, create_temp_building, create_temp_apartment, create_temp_user
    ):
        """
        New owner claims an unowned apartment.
        Expected: 200, apartment.owner set to the caller, status='occupied'.
        """
        from core.api_client import APIClient

        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
        )

        # Create a fresh owner and authenticate
        owner = create_temp_user(role="owner")
        owner_client = APIClient(env_config.api_url)
        owner_client.authenticate(owner["email"], owner["password"])

        apartment_api = ApartmentAPI(owner_client)
        resp = apartment_api.claim(apt["id"])
        assert resp.status_code == 200, (
            f"Owner claiming a vacant apartment must return 200, "
            f"got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["status"] == "occupied", (
            f"Claimed apartment status must be 'occupied', got '{body.get('status')}'"
        )
        assert str(body["owner_id"]) == str(owner["id"]), (
            "Claimed apartment owner_id must match the requesting user"
        )
        owner_client.logout()

    def test_claim_auto_joins_building(
        self, env_config, create_temp_building, create_temp_apartment, create_temp_user
    ):
        """
        After claiming an apartment, the owner must automatically be a member of
        the building (GET /buildings/{id}/ returns 200 for that owner).
        """
        from core.api_client import APIClient

        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
        )

        owner = create_temp_user(role="owner")
        owner_client = APIClient(env_config.api_url)
        owner_client.authenticate(owner["email"], owner["password"])

        # Claim the apartment — should auto-join the building
        apartment_api = ApartmentAPI(owner_client)
        claim_resp = apartment_api.claim(apt["id"])
        assert claim_resp.status_code == 200, claim_resp.text

        # Owner must now see the building
        building_api_owner = BuildingAPI(owner_client)
        get_resp = building_api_owner.get(building["id"])
        assert get_resp.status_code == 200, (
            f"Owner must be auto-joined to building after claim "
            f"(got {get_resp.status_code})"
        )
        owner_client.logout()


@pytest.mark.negative
class TestApartmentClaimNegative:

    def test_claim_already_owned_apartment_returns_409(
        self, env_config, create_temp_building, create_temp_apartment,
        create_temp_user, owner_with_id
    ):
        """Claiming an apartment that already has an owner must return 409."""
        from core.api_client import APIClient

        _, existing_owner_id = owner_with_id
        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
            owner_id=str(existing_owner_id),
        )

        # A second owner tries to claim the same apartment
        second_owner = create_temp_user(role="owner")
        second_client = APIClient(env_config.api_url)
        second_client.authenticate(second_owner["email"], second_owner["password"])

        apartment_api = ApartmentAPI(second_client)
        resp = apartment_api.claim(apt["id"])
        assert resp.status_code == 409, (
            f"Claiming owned apartment must return 409, "
            f"got {resp.status_code}: {resp.text}"
        )
        second_client.logout()

    def test_admin_cannot_claim_apartment_returns_403(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """Admin-role users must not be able to use the claim endpoint → 403."""
        building = create_temp_building(num_floors=5)
        apt = create_temp_apartment(
            building_id=building["id"],
            num_floors=building["num_floors"],
        )
        apartment_api = ApartmentAPI(admin_api)
        resp = apartment_api.claim(apt["id"])
        assert resp.status_code == 403, (
            f"Admin claiming apartment must return 403, got {resp.status_code}: {resp.text}"
        )

    def test_claim_nonexistent_apartment_returns_404(
        self, env_config, create_temp_user
    ):
        """Claiming a non-existent apartment UUID must return 404."""
        import uuid as _uuid
        from core.api_client import APIClient

        owner = create_temp_user(role="owner")
        owner_client = APIClient(env_config.api_url)
        owner_client.authenticate(owner["email"], owner["password"])

        apartment_api = ApartmentAPI(owner_client)
        resp = apartment_api.claim(str(_uuid.uuid4()))
        assert resp.status_code == 404, (
            f"Claiming non-existent apartment must return 404, got {resp.status_code}"
        )
        owner_client.logout()

    def test_claim_requires_authentication(self, unauthenticated_api):
        """Unauthenticated POST /apartments/{id}/claim/ must return 401."""
        import uuid as _uuid
        apartment_api = ApartmentAPI(unauthenticated_api)
        resp = apartment_api.claim(str(_uuid.uuid4()))
        assert resp.status_code == 401, (
            f"Claim must require authentication (got {resp.status_code})"
        )
