"""API tests for profile and password management."""

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config.settings import settings
from utils.data_factory import generate_password


@pytest.mark.api
class TestProfileUpdate:

    def test_get_profile(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/auth/profile/")
        assert resp.status == 200
        body = resp.json()
        assert "email" in body
        assert "role" in body

    def test_update_profile_name(self, admin_api: APIRequestContext):
        resp = admin_api.patch(
            "/api/v1/auth/profile/",
            data={"first_name": "TestUpdated"},
        )
        assert resp.status == 200
        assert resp.json()["first_name"] == "TestUpdated"

    def test_update_profile_phone(self, admin_api: APIRequestContext):
        resp = admin_api.patch(
            "/api/v1/auth/profile/",
            data={"phone": "+201234567890"},
        )
        assert resp.status == 200

    def test_change_password_success(
        self, playwright: Playwright, create_user
    ):
        user = create_user(role="owner")
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Content-Type": "application/json"},
        )
        try:
            login = ctx.post("/api/v1/auth/login/", data={
                "email": user["email"], "password": user["_password"],
            }).json()
            new_pw = generate_password()
            resp = ctx.patch(
                "/api/v1/auth/change-password/",
                data={
                    "current_password": user["_password"],
                    "new_password": new_pw,
                    "confirm_password": new_pw,
                },
                headers={"Authorization": f"Bearer {login['access']}"},
            )
            assert resp.status in (200, 204)
        finally:
            ctx.dispose()

    def test_change_password_wrong_current(
        self, playwright: Playwright, create_user
    ):
        user = create_user(role="owner")
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Content-Type": "application/json"},
        )
        try:
            login = ctx.post("/api/v1/auth/login/", data={
                "email": user["email"], "password": user["_password"],
            }).json()
            resp = ctx.patch(
                "/api/v1/auth/change-password/",
                data={
                    "current_password": "WrongCurrent!1",
                    "new_password": "NewPass@123!",
                    "confirm_password": "NewPass@123!",
                },
                headers={"Authorization": f"Bearer {login['access']}"},
            )
            assert resp.status == 400
        finally:
            ctx.dispose()

    def test_change_password_mismatch(
        self, playwright: Playwright, create_user
    ):
        user = create_user(role="owner")
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Content-Type": "application/json"},
        )
        try:
            login = ctx.post("/api/v1/auth/login/", data={
                "email": user["email"], "password": user["_password"],
            }).json()
            resp = ctx.patch(
                "/api/v1/auth/change-password/",
                data={
                    "current_password": user["_password"],
                    "new_password": "NewPass@123!",
                    "confirm_password": "Different@123!",
                },
                headers={"Authorization": f"Bearer {login['access']}"},
            )
            assert resp.status == 400
        finally:
            ctx.dispose()

    def test_change_password_weak(
        self, playwright: Playwright, create_user
    ):
        user = create_user(role="owner")
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Content-Type": "application/json"},
        )
        try:
            login = ctx.post("/api/v1/auth/login/", data={
                "email": user["email"], "password": user["_password"],
            }).json()
            resp = ctx.patch(
                "/api/v1/auth/change-password/",
                data={
                    "current_password": user["_password"],
                    "new_password": "short",
                    "confirm_password": "short",
                },
                headers={"Authorization": f"Bearer {login['access']}"},
            )
            assert resp.status == 400
        finally:
            ctx.dispose()
