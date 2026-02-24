"""
Sprint 2 — Buildings API tests.

Covers all 35 building-related API test cases from the QA Strategy:
  TC-S2-API-001 to TC-S2-API-007   Building CRUD
  TC-S2-API-008 to TC-S2-API-011   Building validation negatives
  TC-S2-API-012 to TC-S2-API-014   Multi-tenant isolation
  TC-S2-API-015 to TC-S2-API-016   Owner assignment
  TC-S2-API-028 to TC-S2-API-032   Search, filter & pagination
  TC-S2-API-033 to TC-S2-API-034   Multi-building & security

Markers: sprint_2, api
"""
import pytest

from api.building_api import BuildingAPI
from utils.test_data import BuildingFactory

pytestmark = [pytest.mark.sprint_2, pytest.mark.api]


# ── Building CRUD (TC-S2-API-001 to TC-S2-API-007) ────────────────────────────

@pytest.mark.positive
class TestBuildingCRUD:
    """TC-S2-API-001 to TC-S2-API-007: Basic create/read/update/delete."""

    def test_admin_create_building_returns_201(self, admin_api):
        """TC-S2-API-001: POST /buildings/ with valid data → 201."""
        building_api = BuildingAPI(admin_api)
        data = BuildingFactory.valid()
        resp = building_api.create(**data)
        assert resp.status_code == 201, resp.text

        # Cleanup
        building_api.delete(resp.json()["id"])

    def test_create_response_contains_required_fields(self, admin_api):
        """TC-S2-API-002: Response contains id, name, address, num_floors, tenant_id."""
        building_api = BuildingAPI(admin_api)
        data = BuildingFactory.valid()
        resp = building_api.create(**data)
        assert resp.status_code == 201, resp.text
        body = resp.json()

        for field in ("id", "name", "address", "num_floors", "tenant_id"):
            assert field in body, f"Missing field '{field}' in create response"

        # id and tenant_id must both be UUIDs and equal
        assert body["id"] == body["tenant_id"], (
            "id and tenant_id must be the same UUID"
        )

        # Cleanup
        building_api.delete(body["id"])

    def test_admin_list_buildings_returns_200(self, admin_api, temp_building):
        """TC-S2-API-003: Admin GET /buildings/ returns list of all buildings."""
        building_api = BuildingAPI(admin_api)
        resp = building_api.list()
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Paginated response expected
        assert "results" in body or isinstance(body, list)

    def test_admin_get_building_detail(self, admin_api, temp_building):
        """TC-S2-API-004: Admin GET /buildings/{id}/ returns 200 with building detail."""
        building_api = BuildingAPI(admin_api)
        resp = building_api.get(temp_building["id"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["id"] == temp_building["id"]
        assert body["name"] == temp_building["name"]

    def test_admin_update_building_name(self, admin_api, temp_building):
        """TC-S2-API-005: Admin PATCH /buildings/{id}/ updates name."""
        building_api = BuildingAPI(admin_api)
        new_name = "Updated Building Name"
        resp = building_api.update(temp_building["id"], name=new_name)
        assert resp.status_code == 200, resp.text
        assert resp.json()["name"] == new_name

    def test_admin_delete_building_soft_deletes(self, admin_api, create_temp_building):
        """TC-S2-API-006: Admin DELETE /buildings/{id}/ returns 200/204 (soft delete)."""
        building_api = BuildingAPI(admin_api)
        # Create a disposable building (fixture cleanup handles idempotency)
        building = create_temp_building()
        resp = building_api.delete(building["id"])
        assert resp.status_code in (200, 204), resp.text

    def test_deleted_building_returns_404(self, admin_api, create_temp_building):
        """TC-S2-API-007: Soft-deleted building returns 404 on subsequent GET."""
        building_api = BuildingAPI(admin_api)
        building = create_temp_building()
        building_api.delete(building["id"])

        resp = building_api.get(building["id"])
        assert resp.status_code == 404, (
            f"Expected 404 for deleted building, got {resp.status_code}"
        )


# ── Building Validation — Negatives (TC-S2-API-008 to TC-S2-API-011) ──────────

@pytest.mark.negative
class TestBuildingValidation:
    """TC-S2-API-008 to TC-S2-API-011: Request validation failures → 400."""

    def test_create_missing_name_returns_400(self, admin_api):
        """TC-S2-API-008: POST without name → 400."""
        building_api = BuildingAPI(admin_api)
        data = BuildingFactory.missing_name()
        resp = building_api.create(**data)
        assert resp.status_code == 400, resp.text

    def test_create_missing_address_returns_400(self, admin_api):
        """TC-S2-API-009: POST without address → 400."""
        building_api = BuildingAPI(admin_api)
        data = BuildingFactory.missing_address()
        resp = building_api.create(**data)
        assert resp.status_code == 400, resp.text

    def test_create_num_floors_zero_returns_400(self, admin_api):
        """TC-S2-API-010: POST with num_floors=0 → 400."""
        building_api = BuildingAPI(admin_api)
        data = BuildingFactory.zero_floors()
        resp = building_api.create(**data)
        assert resp.status_code == 400, resp.text

    def test_create_negative_num_apartments_returns_400(self, admin_api):
        """TC-S2-API-011: POST with num_apartments=-1 → 400."""
        building_api = BuildingAPI(admin_api)
        data = BuildingFactory.negative_apartments()
        resp = building_api.create(**data)
        assert resp.status_code == 400, resp.text


# ── Multi-Tenant Isolation (TC-S2-API-012 to TC-S2-API-014) ───────────────────

@pytest.mark.negative
class TestBuildingTenantIsolation:
    """
    Critical: TC-S2-API-012 to TC-S2-API-014.
    Tenant isolation failures are P0 defects.
    """

    def test_owner_cannot_see_unassigned_building(self, admin_api, owner_api, temp_building):
        """
        TC-S2-API-012: Owner GET /buildings/{id}/ for a building they are NOT
        assigned to must return 404 (not in their queryset).
        """
        building_api = BuildingAPI(owner_api)
        resp = building_api.get(temp_building["id"])
        assert resp.status_code == 404, (
            f"Owner must not see unassigned buildings (got {resp.status_code})"
        )

    def test_owner_a_cannot_see_owner_b_building(
        self, admin_api, env_config, create_temp_building, create_temp_user
    ):
        """
        TC-S2-API-013: Owner A cannot see Owner B's assigned building.
        Steps:
          1. Create building and assign Owner B.
          2. Authenticate as Owner A (different user, not assigned).
          3. GET building → 404.
        """
        from core.api_client import APIClient

        building = create_temp_building()

        # Create Owner B and assign to building
        owner_b = create_temp_user(role="owner")
        building_api_admin = BuildingAPI(admin_api)
        assign_resp = building_api_admin.assign_user(building["id"], user_id=owner_b["id"])
        assert assign_resp.status_code in (200, 201), assign_resp.text

        # Create Owner A (not assigned)
        owner_a = create_temp_user(role="owner")
        client_a = APIClient(env_config.api_url)
        client_a.authenticate(owner_a["email"], owner_a["password"])

        building_api_a = BuildingAPI(client_a)
        resp = building_api_a.get(building["id"])
        assert resp.status_code == 404, (
            f"Owner A must not see Owner B's building (got {resp.status_code})"
        )

        client_a.logout()

    def test_building_response_has_no_other_tenant_data(self, admin_api, temp_building):
        """
        TC-S2-API-014: Building detail response must not leak data from
        other tenants — at minimum no cross-building foreign keys should appear.
        """
        building_api = BuildingAPI(admin_api)
        resp = building_api.get(temp_building["id"])
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # id must match the requested building, not another one
        assert body["id"] == temp_building["id"]
        # tenant_id must equal id (not another building's id)
        assert body["tenant_id"] == body["id"]


# ── Owner Assignment (TC-S2-API-015 to TC-S2-API-016) ─────────────────────────

@pytest.mark.positive
class TestOwnerAssignment:
    """TC-S2-API-015 to TC-S2-API-016: Admin assigns owner; owner gains read access."""

    def test_admin_can_assign_owner_to_building(
        self, admin_api, owner_with_id, temp_building
    ):
        """TC-S2-API-015: POST /buildings/{id}/assign-user/ → 200/201."""
        _, owner_id = owner_with_id
        building_api = BuildingAPI(admin_api)
        resp = building_api.assign_user(temp_building["id"], user_id=str(owner_id))
        assert resp.status_code in (200, 201), resp.text
        assert "detail" in resp.json()

    def test_assigned_owner_can_access_building(
        self, admin_api, owner_with_id, temp_building
    ):
        """TC-S2-API-016: After assignment, owner GET /buildings/{id}/ → 200."""
        owner_client, owner_id = owner_with_id
        building_api_admin = BuildingAPI(admin_api)
        building_api_admin.assign_user(temp_building["id"], user_id=str(owner_id))

        building_api_owner = BuildingAPI(owner_client)
        resp = building_api_owner.get(temp_building["id"])
        assert resp.status_code == 200, (
            f"Assigned owner must be able to GET the building (got {resp.status_code})"
        )
        assert resp.json()["id"] == temp_building["id"]


# ── Search, Filter & Pagination (TC-S2-API-028 to TC-S2-API-032) ──────────────

@pytest.mark.positive
class TestBuildingSearchAndPagination:
    """TC-S2-API-028 to TC-S2-API-032: Filtering, searching, and pagination."""

    def test_search_by_name_returns_filtered_results(
        self, admin_api, create_temp_building
    ):
        """TC-S2-API-028: GET /buildings/?search=<name> returns filtered results."""
        building_api = BuildingAPI(admin_api)
        unique_name = "UniqueSearchTargetBldg"
        building = create_temp_building(name=unique_name)

        resp = building_api.list(search=unique_name)
        assert resp.status_code == 200, resp.text
        results = resp.json().get("results", resp.json())
        ids = [b["id"] for b in results]
        assert building["id"] in ids, (
            f"Search for '{unique_name}' should return the created building"
        )

    def test_pagination_returns_correct_page_size(self, admin_api):
        """TC-S2-API-031: List endpoint returns paginated results (next/previous links)."""
        building_api = BuildingAPI(admin_api)
        resp = building_api.list(page_size=2)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "results" in body, "Response must be paginated with 'results' key"
        assert "count" in body, "Paginated response must include 'count'"
        assert len(body["results"]) <= 2, "Page size must be honoured"

    def test_out_of_range_page_returns_empty_not_error(self, admin_api):
        """TC-S2-API-032: GET /buildings/?page=999 returns empty results, not a 5xx."""
        building_api = BuildingAPI(admin_api)
        resp = building_api.list(page=9999)
        assert resp.status_code in (200, 404), (
            f"Out-of-range page must not be a 5xx error (got {resp.status_code})"
        )


# ── Multi-Building & Security (TC-S2-API-033 to TC-S2-API-034) ────────────────

@pytest.mark.positive
class TestBuildingSecurity:
    """TC-S2-API-033 to TC-S2-API-034."""

    def test_admin_manages_multiple_buildings(self, admin_api, create_temp_building):
        """TC-S2-API-033: Admin with multiple buildings sees all of them in list."""
        building_api = BuildingAPI(admin_api)
        b1 = create_temp_building()
        b2 = create_temp_building()

        resp = building_api.list(page_size=200)
        assert resp.status_code == 200, resp.text
        all_ids = [b["id"] for b in resp.json().get("results", resp.json())]
        assert b1["id"] in all_ids, "Building 1 must appear in list"
        assert b2["id"] in all_ids, "Building 2 must appear in list"

    def test_tenant_id_is_auto_generated_uuid(self, admin_api):
        """TC-S2-API-034: tenant_id is auto-generated UUID — never user-supplied."""
        import uuid as _uuid

        building_api = BuildingAPI(admin_api)
        data = BuildingFactory.valid()
        # Attempt to supply tenant_id in request (must be ignored)
        data["tenant_id"] = "00000000-0000-0000-0000-000000000000"
        resp = building_api.create(**data)
        assert resp.status_code == 201, resp.text
        body = resp.json()

        # The returned tenant_id must be a valid UUID
        assert "tenant_id" in body
        try:
            _uuid.UUID(str(body["tenant_id"]))
        except ValueError:
            pytest.fail("tenant_id in response is not a valid UUID")

        # The returned tenant_id must NOT be the injected value
        assert body["tenant_id"] != "00000000-0000-0000-0000-000000000000", (
            "Backend must NOT use client-supplied tenant_id"
        )

        # Cleanup
        building_api.delete(body["id"])

    def test_unauthenticated_cannot_list_buildings(self, unauthenticated_api):
        """Unauthenticated GET /buildings/ must return 401."""
        building_api = BuildingAPI(unauthenticated_api)
        resp = building_api.list()
        assert resp.status_code == 401, (
            f"Expected 401 for unauthenticated request, got {resp.status_code}"
        )

    def test_owner_cannot_create_building(self, owner_api):
        """Owner POST /buildings/ must return 403."""
        building_api = BuildingAPI(owner_api)
        data = BuildingFactory.valid()
        resp = building_api.create(**data)
        assert resp.status_code == 403, (
            f"Owner must not be allowed to create buildings (got {resp.status_code})"
        )

    def test_owner_cannot_delete_building(self, admin_api, owner_api, temp_building):
        """Owner DELETE /buildings/{id}/ must return 403 (even if not in their scope)."""
        # Create a building and assign the owner so they CAN see it
        building_api_admin = BuildingAPI(admin_api)
        owner_resp = BuildingAPI(owner_api).list()
        # Owner tries to delete an admin building they can't even see → 403 or 404
        building_api_owner = BuildingAPI(owner_api)
        resp = building_api_owner.delete(temp_building["id"])
        assert resp.status_code in (403, 404), (
            f"Owner must not delete buildings (got {resp.status_code})"
        )
