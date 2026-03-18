"""Production smoke test suite — 15 quick post-deploy checks."""
import pytest
from config.settings import settings


@pytest.mark.smoke
class TestProductionSmoke:
    def test_login_works(self, api_context):
        resp = api_context.post("/api/v1/auth/login/", data={
            "email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD,
        })
        assert resp.status == 200

    def test_list_buildings(self, admin_api):
        assert admin_api.get("/api/v1/buildings/").status == 200

    def test_list_apartments(self, admin_api):
        assert admin_api.get("/api/v1/apartments/").status == 200

    def test_list_expenses(self, admin_api):
        assert admin_api.get("/api/v1/expenses/").status == 200

    def test_list_payments(self, admin_api):
        assert admin_api.get("/api/v1/payments/").status == 200

    def test_list_notifications(self, admin_api):
        assert admin_api.get("/api/v1/notifications/").status == 200

    def test_list_categories(self, admin_api):
        assert admin_api.get("/api/v1/expenses/categories/").status == 200

    def test_list_audit_logs(self, admin_api):
        assert admin_api.get("/api/v1/audit/").status == 200

    def test_admin_dashboard(self, admin_api):
        assert admin_api.get("/api/v1/dashboard/admin/").status == 200

    def test_owner_dashboard(self, owner_api):
        assert owner_api.get("/api/v1/dashboard/owner/").status == 200

    def test_profile(self, admin_api):
        assert admin_api.get("/api/v1/auth/profile/").status == 200

    def test_export_csv(self, admin_api):
        resp = admin_api.get("/api/v1/exports/payments/", params={"format": "csv"})
        assert resp.status == 200

    def test_owner_cannot_access_admin_endpoints(self, owner_api):
        assert owner_api.get("/api/v1/users/").status == 403

    def test_ui_login_page_loads(self, page):
        page.goto(f"{settings.BASE_URL}/login")
        page.wait_for_load_state("networkidle")
        assert page.get_by_role("button", name="Sign in").is_visible()

    def test_ui_dashboard_loads_after_login(self, admin_page):
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        assert "/dashboard" in admin_page.url
