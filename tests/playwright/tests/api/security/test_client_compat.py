"""API tests for mobile/PWA client compatibility.

Ported from the retired selenium-legacy sprint_7 suite: mobile user-agent,
JSON error bodies, gzip, payload size, concurrency and per-user rate limits.
"""

from concurrent.futures import ThreadPoolExecutor

import pytest
import requests
from playwright.sync_api import APIRequestContext

from config.settings import settings

_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "Chrome/120 Mobile Safari/537.36"
)
_MAX_PAYLOAD_BYTES = 204_800  # 200 KB
_NULL_UUID = "00000000-0000-0000-0000-000000000000"


@pytest.mark.api
class TestClientCompat:

    @pytest.mark.positive
    @pytest.mark.parametrize(
        "path", ["/buildings/", "/apartments/", "/expenses/", "/notifications/"]
    )
    def test_mobile_user_agent_accepted(self, admin_api, path):
        resp = admin_api.get(path, headers={"User-Agent": _MOBILE_UA})
        assert resp.status in (200, 204), f"{path}: {resp.status}"

    @pytest.mark.negative
    def test_invalid_token_returns_json_401(self, api_context: APIRequestContext):
        resp = api_context.get(
            "/api/v1/buildings/",
            headers={"Authorization": "Bearer invalid_token_xyz"},
        )
        assert resp.status == 401
        assert "application/json" in resp.headers.get("content-type", "")

    @pytest.mark.negative
    def test_missing_resource_returns_json_404(self, admin_api):
        resp = admin_api.get(
            f"/buildings/{_NULL_UUID}/", headers={"Accept": "application/json"}
        )
        assert resp.status == 404
        assert "application/json" in resp.headers.get("content-type", "")

    @pytest.mark.positive
    def test_gzip_accept_encoding_ok(self, admin_api):
        resp = admin_api.get(
            "/buildings/", headers={"Accept-Encoding": "gzip, deflate"}
        )
        assert resp.status == 200
        assert resp.json() is not None

    @pytest.mark.positive
    @pytest.mark.parametrize("path", ["/buildings/", "/apartments/", "/notifications/"])
    def test_list_payload_under_200kb(self, admin_api, path):
        resp = admin_api.get(path)
        assert resp.status == 200
        size = len(resp.body())
        assert size < _MAX_PAYLOAD_BYTES, f"{path}: {size} bytes"

    @pytest.mark.positive
    def test_concurrent_requests_consistent(self, admin_api):
        # Playwright's sync API is thread-bound, so use requests in workers.
        url = f"{settings.API_BASE_URL}/api/v1/notifications/"
        headers = {"Authorization": f"Bearer {admin_api._access_token}"}

        def _get(_):
            return requests.get(url, headers=headers, timeout=15).status_code

        with ThreadPoolExecutor(max_workers=5) as pool:
            codes = list(pool.map(_get, range(5)))
        assert codes == [200] * 5, codes

    @pytest.mark.positive
    def test_rate_limit_is_per_user(self, admin_api, owner_api: APIRequestContext):
        admin_codes = [admin_api.get("/buildings/").status for _ in range(3)]
        owner_codes = [
            owner_api.get("/api/v1/notifications/").status for _ in range(3)
        ]
        assert 429 not in admin_codes, admin_codes
        assert 429 not in owner_codes, owner_codes
