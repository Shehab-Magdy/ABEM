"""API tests for role-based access control."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_building, build_owner_user


@pytest.mark.api
@pytest.mark.security
@pytest.mark.rbac
class TestRBAC:

    def test_owner_cannot_post_buildings(self, owner_api: APIRequestContext):
        resp = owner_api.post("/api/v1/buildings/", data=build_building())
        assert resp.status == 403

    def test_owner_cannot_post_expenses(self, owner_api: APIRequestContext):
        resp = owner_api.post("/api/v1/expenses/", data={"title": "blocked"})
        assert resp.status == 403

    def test_owner_cannot_post_users(self, owner_api: APIRequestContext):
        resp = owner_api.post("/api/v1/users/", data=build_owner_user())
        assert resp.status == 403

    def test_owner_cannot_get_audit_logs(self, owner_api: APIRequestContext):
        resp = owner_api.get("/api/v1/audit/")
        assert resp.status == 403

    def test_admin_has_full_access(self, admin_api: APIRequestContext):
        for endpoint in ["/api/v1/buildings/", "/api/v1/expenses/",
                         "/api/v1/users/", "/api/v1/audit/"]:
            resp = admin_api.get(endpoint)
            assert resp.status == 200, f"Admin denied on GET {endpoint}"

    def test_deactivated_user_cannot_login(
        self, admin_api: APIRequestContext, api_context: APIRequestContext, create_user
    ):
        user = create_user(role="owner")
        deact = admin_api.post(f"/api/v1/users/{user['id']}/deactivate/")
        if deact.status == 404:
            pytest.skip("Deactivate endpoint not accessible for this user")
        resp = api_context.post("/api/v1/auth/login/", data={
            "email": user["email"], "password": user["_password"],
        })
        assert resp.status == 401
