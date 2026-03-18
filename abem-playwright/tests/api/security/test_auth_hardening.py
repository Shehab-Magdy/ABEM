"""API tests for JWT auth hardening."""

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config.settings import settings
from utils.jwt_helpers import (
    build_expired_token,
    build_none_alg_token,
    build_tampered_token,
)


@pytest.mark.api
@pytest.mark.security
class TestAuthHardening:

    def test_tampered_role_token_rejected(
        self, playwright: Playwright, admin_token: str
    ):
        tampered = build_tampered_token(admin_token, {"role": "superadmin"})
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Authorization": f"Bearer {tampered}"},
        )
        try:
            resp = ctx.get("/api/v1/buildings/")
            assert resp.status == 401
        finally:
            ctx.dispose()

    def test_wrong_secret_token_rejected(
        self, playwright: Playwright, admin_token: str
    ):
        tampered = build_tampered_token(admin_token, {})
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Authorization": f"Bearer {tampered}"},
        )
        try:
            resp = ctx.get("/api/v1/buildings/")
            assert resp.status == 401
        finally:
            ctx.dispose()

    def test_none_alg_token_rejected(
        self, playwright: Playwright, admin_token: str
    ):
        none_token = build_none_alg_token(admin_token)
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Authorization": f"Bearer {none_token}"},
        )
        try:
            resp = ctx.get("/api/v1/buildings/")
            assert resp.status == 401
        finally:
            ctx.dispose()

    def test_expired_token_rejected(
        self, playwright: Playwright, admin_token: str
    ):
        expired = build_expired_token(admin_token)
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Authorization": f"Bearer {expired}"},
        )
        try:
            resp = ctx.get("/api/v1/buildings/")
            assert resp.status == 401
        finally:
            ctx.dispose()

    def test_missing_auth_header(self, unauthenticated_api: APIRequestContext):
        resp = unauthenticated_api.get("/api/v1/buildings/")
        assert resp.status == 401

    def test_blacklisted_token_after_logout(self, playwright: Playwright):
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Content-Type": "application/json"},
        )
        try:
            login = ctx.post("/api/v1/auth/login/", data={
                "email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD,
            }).json()
            ctx.post("/api/v1/auth/logout/", data={
                "refresh": login["refresh"],
            }, headers={"Authorization": f"Bearer {login['access']}"})
            # Refresh with old token should fail
            resp = ctx.post("/api/v1/auth/refresh/", data={
                "refresh": login["refresh"],
            })
            assert resp.status == 401
        finally:
            ctx.dispose()
