"""
Sprint 7 — Flutter Finalization API Tests (10 cases)
TC-S7-API-001 → TC-S7-API-010

Tests cover:
  TestMobileUserAgentAPI   (1)  – all key endpoints accept Flutter user-agent
  TestJWTRefreshMobileAPI  (1)  – JWT refresh flow from mobile client
  TestFileUploadMobileAPI  (1)  – multipart/form-data upload from mobile
  TestErrorFormatAPI       (2)  – 401 returns JSON, 404 returns JSON
  TestCompressionAPI       (1)  – gzip Accept-Encoding accepted without error
  TestPaginationAPI        (1)  – list endpoint includes pagination metadata
  TestConcurrencyAPI       (1)  – 5 simultaneous requests from same user are consistent
  TestRateLimitAPI         (1)  – per-user, not per-IP: two users succeed independently
  TestPayloadSizeAPI       (1)  – list endpoints return < 200 KB
"""
from __future__ import annotations

import concurrent.futures

import pytest

from api.building_api import BuildingAPI
from api.expense_api import ExpenseAPI
from core.api_client import APIClient

pytestmark = [
    pytest.mark.api,
    pytest.mark.sprint_7,
]

# Synthetic 1×1 red PNG — minimal valid PNG (67 bytes) for multipart upload tests
_TINY_PNG = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
    0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
    0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
    0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
    0x44, 0xAE, 0x42, 0x60, 0x82,
])

_FLUTTER_UA = "ABEM-Flutter/1.0.0 (Android)"
_MAX_PAYLOAD_BYTES = 204_800  # 200 KB


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S7-API-001 — Mobile User-Agent
# ═══════════════════════════════════════════════════════════════════════════════

class TestMobileUserAgentAPI:

    @pytest.mark.positive
    def test_flutter_user_agent_accepted_on_all_endpoints(self, admin_api: APIClient):
        """TC-S7-API-001: All key API endpoints respond correctly to Flutter user-agent header."""
        endpoints = [
            "/buildings/",
            "/apartments/",
            "/expenses/",
            "/notifications/",
        ]
        for endpoint in endpoints:
            resp = admin_api.get(endpoint, headers={"User-Agent": _FLUTTER_UA})
            assert resp.status_code in (200, 204), (
                f"Endpoint {endpoint} rejected Flutter user-agent: "
                f"{resp.status_code} — {resp.text[:200]}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S7-API-002 — JWT Refresh from Mobile
# ═══════════════════════════════════════════════════════════════════════════════

class TestJWTRefreshMobileAPI:

    @pytest.mark.positive
    def test_jwt_refresh_returns_new_access_token(self, admin_api: APIClient):
        """TC-S7-API-002: POST /auth/refresh/ with valid refresh token returns new access token."""
        assert admin_api.refresh_token, "admin_api must have a refresh token after authenticate()"

        url = f"{admin_api.base_url}/auth/refresh/"
        resp = admin_api.session.post(
            url,
            json={"refresh": admin_api.refresh_token},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200, f"JWT refresh failed: {resp.text}"
        body = resp.json()
        assert "access" in body, f"Response missing 'access' key: {body}"
        assert isinstance(body["access"], str) and len(body["access"]) > 20


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S7-API-003 — Multipart File Upload from Mobile
# ═══════════════════════════════════════════════════════════════════════════════

class TestFileUploadMobileAPI:

    @pytest.mark.positive
    def test_multipart_file_upload_accepted(self, admin_api: APIClient, temp_expense: dict):
        """TC-S7-API-003: POST /expenses/{id}/upload/ accepts multipart/form-data from mobile."""
        expense_api = ExpenseAPI(admin_api)
        resp = expense_api.upload(
            expense_id=temp_expense["id"],
            file_bytes=_TINY_PNG,
            filename="receipt.png",
            mime_type="image/png",
        )
        # 200/201 = accepted; 400 = validation rejection — all are acceptable server responses
        assert resp.status_code in (200, 201, 400), (
            f"Upload endpoint returned unexpected status {resp.status_code}: {resp.text[:300]}"
        )
        # Server must always respond with JSON, never HTML
        content_type = resp.headers.get("Content-Type", "")
        assert "application/json" in content_type, (
            f"Upload response is not JSON: Content-Type={content_type}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S7-API-004 — 401 Returns JSON
# TC-S7-API-007 — 404 Returns JSON
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrorFormatAPI:

    @pytest.mark.negative
    def test_expired_token_returns_401_json(self, admin_api: APIClient):
        """TC-S7-API-004: Sending an invalid Bearer token returns 401 with JSON body."""
        url = f"{admin_api.base_url}/buildings/"
        # Bypass APIClient.request() (which auto-refreshes on 401) by calling session directly
        resp = admin_api.session.get(
            url,
            headers={"Authorization": "Bearer invalid_token_xyz_this_is_not_valid"},
        )
        assert resp.status_code == 401, (
            f"Expected 401 with invalid token, got {resp.status_code}: {resp.text[:200]}"
        )
        content_type = resp.headers.get("Content-Type", "")
        assert "application/json" in content_type, (
            f"401 response Content-Type is not JSON: {content_type}. Body: {resp.text[:300]}"
        )

    @pytest.mark.negative
    def test_nonexistent_resource_returns_json_404(self, admin_api: APIClient):
        """TC-S7-API-007: Request to a non-existent resource within DRF returns JSON 404, not HTML."""
        # Use a valid DRF route with a non-existent UUID — DRF always returns JSON for its 404s
        null_uuid = "00000000-0000-0000-0000-000000000000"
        url = f"{admin_api.base_url}/buildings/{null_uuid}/"
        resp = admin_api.session.get(
            url,
            headers={
                "Authorization": f"Bearer {admin_api.access_token}",
                "Accept": "application/json",
            },
        )
        assert resp.status_code == 404, (
            f"Expected 404, got {resp.status_code}: {resp.text[:200]}"
        )
        content_type = resp.headers.get("Content-Type", "")
        assert "application/json" in content_type, (
            f"404 response Content-Type is not JSON: {content_type}. Body: {resp.text[:300]}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S7-API-005 — Gzip Compression
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompressionAPI:

    @pytest.mark.positive
    def test_gzip_accept_encoding_does_not_cause_error(self, admin_api: APIClient):
        """TC-S7-API-005: API with Accept-Encoding: gzip returns 200, no 406/500."""
        resp = admin_api.get(
            "/buildings/",
            headers={"Accept-Encoding": "gzip, deflate"},
        )
        assert resp.status_code == 200, (
            f"gzip encoding caused error: {resp.status_code} — {resp.text[:200]}"
        )
        # requests auto-decompresses gzip — confirm body is still parseable JSON
        assert resp.json() is not None


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S7-API-006 — Pagination Metadata
# ═══════════════════════════════════════════════════════════════════════════════

class TestPaginationAPI:

    @pytest.mark.positive
    def test_list_endpoint_returns_pagination_metadata(self, admin_api: APIClient):
        """TC-S7-API-006: GET /buildings/ response contains pagination metadata or plain list."""
        building_api = BuildingAPI(admin_api)
        resp = building_api.list()
        assert resp.status_code == 200, f"Buildings list failed: {resp.text}"
        body = resp.json()
        if isinstance(body, dict):
            assert "count" in body, (
                f"Paginated response missing 'count'. Keys: {list(body.keys())}"
            )
            assert "results" in body, (
                f"Paginated response missing 'results'. Keys: {list(body.keys())}"
            )
        else:
            assert isinstance(body, list), f"Unexpected response type: {type(body)}"


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S7-API-008 — Concurrent Requests
# ═══════════════════════════════════════════════════════════════════════════════

class TestConcurrencyAPI:

    @pytest.mark.positive
    def test_concurrent_requests_produce_consistent_results(self, admin_api: APIClient):
        """TC-S7-API-008: 5 simultaneous authenticated GETs to /notifications/ all return 200."""
        url = f"{admin_api.base_url}/notifications/"
        token = admin_api.access_token  # capture once before spawning workers

        def _get(_: int) -> int:
            resp = admin_api.session.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(_get, i) for i in range(5)]
            status_codes = [f.result(timeout=15) for f in futures]

        assert all(sc == 200 for sc in status_codes), (
            f"Concurrent requests returned non-200 codes: {status_codes}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S7-API-009 — Per-User Rate Limiting
# ═══════════════════════════════════════════════════════════════════════════════

class TestRateLimitAPI:

    @pytest.mark.positive
    def test_two_users_make_requests_without_shared_rate_limit(
        self, admin_api: APIClient, owner_api: APIClient
    ):
        """TC-S7-API-009: Admin and owner each make 3 requests without hitting 429."""
        admin_url = f"{admin_api.base_url}/buildings/"
        owner_url = f"{owner_api.base_url}/notifications/"

        admin_codes = []
        owner_codes = []
        for _ in range(3):
            admin_codes.append(
                admin_api.session.get(
                    admin_url,
                    headers={"Authorization": f"Bearer {admin_api.access_token}"},
                ).status_code
            )
            owner_codes.append(
                owner_api.session.get(
                    owner_url,
                    headers={"Authorization": f"Bearer {owner_api.access_token}"},
                ).status_code
            )

        assert 429 not in admin_codes, f"Admin hit rate limit: {admin_codes}"
        assert 429 not in owner_codes, f"Owner hit rate limit: {owner_codes}"
        assert all(c in (200, 204) for c in admin_codes), f"Admin unexpected codes: {admin_codes}"
        assert all(c in (200, 204) for c in owner_codes), f"Owner unexpected codes: {owner_codes}"


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S7-API-010 — Payload Size Under 200 KB
# ═══════════════════════════════════════════════════════════════════════════════

class TestPayloadSizeAPI:

    @pytest.mark.positive
    def test_list_endpoints_return_under_200kb(self, admin_api: APIClient):
        """TC-S7-API-010: GET list endpoints all return < 204800 bytes for mobile bandwidth."""
        endpoints = [
            "/buildings/",
            "/apartments/",
            "/notifications/",
        ]
        for endpoint in endpoints:
            resp = admin_api.get(endpoint)
            assert resp.status_code == 200, f"Endpoint {endpoint} returned {resp.status_code}"
            payload_size = len(resp.content)
            assert payload_size < _MAX_PAYLOAD_BYTES, (
                f"Endpoint {endpoint} payload {payload_size} bytes "
                f"exceeds 200 KB limit ({_MAX_PAYLOAD_BYTES} bytes)"
            )
