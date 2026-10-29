"""Sprint 9 — Security (OWASP Top 10) tests.

Covers TC-S9-SEC-001 to SEC-015 (15 test cases).

Tests that require infrastructure or configuration not available in this
environment are skip-guarded:
  - SEC-004: TLS enforcement (dev server has no TLS)
  - SEC-009: Server-side log inspection (not possible from test client)
  - SEC-010: ALLOWED_HOSTS (DEBUG=True in dev disables host checking)
  - SEC-011: Rate limiting (not configured on this environment)
  - SEC-012: File-upload executable scan (no dedicated endpoint)
  - SEC-014: SSRF via URL upload (no URL-based upload endpoint)

All remaining 8 security tests exercise the live API.
"""
from __future__ import annotations

import base64
import json

import pytest
import requests as _req

pytestmark = [pytest.mark.api, pytest.mark.sprint_9]

# ── Shared helpers ─────────────────────────────────────────────────────────────


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


# ── OWASP A01 — Broken Access Control ─────────────────────────────────────────


class TestBrokenAccessControl:
    """OWASP A01 — vertical & horizontal privilege escalation."""

    def test_jwt_role_escalation_rejected(self, env_config, owner_api):
        """TC-S9-SEC-001: Owner cannot escalate to Admin by modifying the JWT role claim.

        Tampering with the payload while keeping the original signature makes
        the token invalid. SimpleJWT must reject it with 401/403.
        """
        token = owner_api.access_token
        parts = token.split(".")
        assert len(parts) == 3, "Access token is not a 3-part JWT"

        # Decode payload (add padding)
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))

        # Escalate role
        payload["role"] = "admin"
        tampered_payload = _b64_encode(json.dumps(payload).encode())
        # Keep original header + signature but swap the payload
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

        r = _req.get(
            f"{env_config.api_url}/audit/",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert r.status_code in (401, 403), (
            f"Expected 401/403 for tampered JWT, got {r.status_code} (SEC-001)"
        )

    def test_horizontal_privilege_escalation(self, env_config, sec_data):
        """TC-S9-SEC-002: Owner cannot access another owner's apartment (horizontal IDOR)."""
        r = _req.get(
            f"{env_config.api_url}/apartments/{sec_data['owner_b_apartment_id']}/",
            headers=_auth_headers(sec_data["owner_a_token"]),
        )
        assert r.status_code in (403, 404), (
            f"Expected 403/404 for cross-owner apartment access, got {r.status_code} (SEC-002)"
        )


# ── OWASP A02 — Cryptographic Failures ────────────────────────────────────────


class TestCryptographicFailures:
    """OWASP A02 — sensitive data exposure via weak cryptography."""

    def test_password_not_returned_in_api_response(self, admin_api, env_config):
        """TC-S9-SEC-003: All user API responses omit the password field.

        Verifies that PBKDF2/bcrypt hashes are never serialised to clients.
        """
        r = admin_api.get("/users/")
        data = r.json()
        users = data.get("results", data) if isinstance(data, dict) else data
        for user in users:
            assert "password" not in user, (
                f"User object exposes 'password' field: {list(user.keys())} (SEC-003)"
            )

    def test_tls_older_versions_rejected(self):
        """TC-S9-SEC-004: TLS 1.0 and TLS 1.1 connections are rejected (production)."""
        pytest.skip(
            "TLS version enforcement requires a production-like setup with HTTPS — "
            "dev server runs plain HTTP (SEC-004)"
        )


# ── OWASP A03 — Injection ─────────────────────────────────────────────────────


class TestInjection:
    """OWASP A03 — SQL injection and XSS."""

    def test_sql_injection_returns_400_not_500(self, env_config, admin_api):
        """TC-S9-SEC-005: SQL injection payloads in string inputs return 400, not 500.

        Django's ORM parameterises all queries; injection should be stored safely
        or rejected by validation, never triggering a database error.
        """
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE buildings;--",
            "1; SELECT * FROM auth_user--",
        ]
        for payload in sql_payloads:
            r = _req.post(
                f"{env_config.api_url}/buildings/",
                json={
                    "name": payload,
                    "address": "Test Address",
                    "city": "Cairo",
                    "country": "Egypt",
                    "num_floors": 3,
                    "num_apartments": 2,
                },
                headers=_auth_headers(admin_api.access_token),
                timeout=10,
            )
            assert r.status_code != 500, (
                f"SQL injection payload '{payload}' triggered a 500 error (SEC-005)"
            )

    def test_xss_payload_stored_not_executed(self, env_config, admin_api):
        """TC-S9-SEC-006: XSS payloads in text inputs are stored safely.

        The API returns JSON — the payload must be accepted or rejected cleanly
        (201 or 400) and must never cause a 500 or expose a traceback.
        """
        xss = "<script>alert('xss')</script>"
        r = _req.post(
            f"{env_config.api_url}/buildings/",
            json={
                "name": xss,
                "address": "XSS Test Ave",
                "city": "Cairo",
                "country": "Egypt",
                "num_floors": 3,
                "num_apartments": 2,
            },
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code in (201, 400), (
            f"XSS payload in building name caused unexpected status {r.status_code} (SEC-006)"
        )
        assert "Traceback" not in r.text, (
            "Response body contains a Python traceback (SEC-006)"
        )

        # Cleanup if the building was created
        if r.status_code == 201:
            bid = r.json().get("id")
            if bid:
                _req.delete(
                    f"{env_config.api_url}/buildings/{bid}/",
                    headers=_auth_headers(admin_api.access_token),
                    timeout=10,
                )


# ── OWASP A04 — Insecure Direct Object Reference ──────────────────────────────


class TestInsecureDOR:
    """OWASP A04 — IDOR via predictable resource identifiers."""

    def test_idor_apartment_returns_404_for_non_owner(self, env_config, sec_data):
        """TC-S9-SEC-007: IDOR — /apartments/{id}/ returns 404 for a non-owning user.

        DRF queryset is filtered to `owner=request.user` so the resource is
        simply invisible (404) rather than forbidden (403).
        """
        r = _req.get(
            f"{env_config.api_url}/apartments/{sec_data['owner_b_apartment_id']}/",
            headers=_auth_headers(sec_data["owner_a_token"]),
        )
        assert r.status_code in (403, 404), (
            f"Expected 403/404 for IDOR apartment access, got {r.status_code} (SEC-007)"
        )

    def test_idor_payment_returns_404_for_non_owner(self, env_config, sec_data):
        """TC-S9-SEC-008: IDOR — /payments/{id}/ returns 404 for a non-owning user.

        Payment queryset is filtered to `apartment__owner=request.user`.
        """
        r = _req.get(
            f"{env_config.api_url}/payments/{sec_data['owner_b_payment_id']}/",
            headers=_auth_headers(sec_data["owner_a_token"]),
        )
        assert r.status_code in (403, 404), (
            f"Expected 403/404 for IDOR payment access, got {r.status_code} (SEC-008)"
        )


# ── OWASP A05 / A09 — Security Misconfiguration & Logging ─────────────────────


class TestSecurityMisconfiguration:
    """OWASP A05/A09 — configuration and logging hygiene."""

    def test_no_sensitive_data_in_log_responses(self):
        """TC-S9-SEC-009: No sensitive data (passwords, tokens) in server logs."""
        pytest.skip(
            "Server-side log inspection is not possible from the test client — SEC-009"
        )

    def test_allowed_hosts_restricts_invalid_host_header(self):
        """TC-S9-SEC-010: Django ALLOWED_HOSTS rejects requests with an invalid Host header."""
        pytest.skip(
            "DEBUG=True in development disables ALLOWED_HOSTS enforcement — SEC-010"
        )


# ── OWASP A07 — Authentication / Rate Limiting ────────────────────────────────


class TestAuthRateLimiting:
    """OWASP A07 — authentication and rate-limiting controls."""

    def test_rate_limiting_returns_429_after_threshold(self):
        """TC-S9-SEC-011: Auth endpoint rate-limited to 10 req/min (429 after limit)."""
        pytest.skip(
            "Rate limiting (django-ratelimit / DRF throttle) is not configured on "
            "this environment — SEC-011"
        )

    def test_file_upload_rejects_executable_magic_bytes(self):
        """TC-S9-SEC-012: File uploads are scanned for executable content (magic bytes)."""
        pytest.skip(
            "No dedicated file-upload-with-magic-byte-validation endpoint identified — SEC-012"
        )


# ── OWASP A09 — Logging & Monitoring ──────────────────────────────────────────


class TestLoggingMonitoring:
    """OWASP A09 — error responses must not leak implementation details."""

    def test_500_errors_dont_expose_stack_traces(self, env_config, admin_api):
        """TC-S9-SEC-013: 5xx errors do not expose stack traces or file paths to clients.

        Triggers a 404 on a malformed UUID path to verify the custom exception
        handler (apps.core.exceptions.custom_exception_handler) returns a clean
        JSON response with no Python traceback or internal file paths.
        """
        r = _req.get(
            f"{env_config.api_url}/buildings/not-a-valid-uuid/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        body = r.text
        assert "Traceback" not in body, (
            "Response body contains 'Traceback' — stack trace leaked (SEC-013)"
        )
        assert 'File "' not in body, (
            "Response body contains 'File \"' — file paths leaked (SEC-013)"
        )
        # Confirm the response is properly formatted JSON (not a Django debug page)
        try:
            r.json()
        except Exception:
            pytest.fail(
                f"Response is not valid JSON (likely an HTML debug page): {body[:200]} (SEC-013)"
            )


# ── OWASP A10 — SSRF ──────────────────────────────────────────────────────────


class TestSSRF:
    """OWASP A10 — server-side request forgery."""

    def test_ssrf_file_upload_blocked(self):
        """TC-S9-SEC-014: SSRF — file upload URL parameter cannot be pointed at internal IP."""
        pytest.skip(
            "No URL-based file upload endpoint identified in the current API surface — SEC-014"
        )


# ── JWT Security ───────────────────────────────────────────────────────────────


class TestJWTSecurity:
    """JWT-specific security: algorithm confusion attacks."""

    def test_jwt_none_algorithm_rejected(self, env_config):
        """TC-S9-SEC-015: JWT 'none' algorithm is rejected with 401.

        Crafts a token with {"alg":"none","typ":"JWT"} and an admin payload
        but no signature. SimpleJWT must not accept this token.
        """
        header  = _b64_encode(json.dumps({"alg": "none", "typ": "JWT"}).encode())
        payload = _b64_encode(
            json.dumps(
                {
                    "user_id": "00000000-0000-0000-0000-000000000000",
                    "role": "admin",
                    "exp": 9_999_999_999,
                }
            ).encode()
        )
        none_token = f"{header}.{payload}."  # empty signature

        r = _req.get(
            f"{env_config.api_url}/audit/",
            headers={"Authorization": f"Bearer {none_token}"},
        )
        assert r.status_code == 401, (
            f"Expected 401 for 'alg:none' JWT, got {r.status_code} (SEC-015)"
        )
