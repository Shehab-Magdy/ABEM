"""JWT decode and inspection helpers for auth tests.

Uses PyJWT for decoding without verification (test inspection only).
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any

import jwt


def decode_token_unverified(token: str) -> dict[str, Any]:
    """Decode a JWT without verifying the signature.

    Used for test assertions on claims (role, exp, tenant_ids).
    """
    return jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])


def get_token_claims(token: str) -> dict[str, Any]:
    """Return decoded JWT claims."""
    return decode_token_unverified(token)


def get_token_role(token: str) -> str:
    """Extract the role claim from a JWT."""
    claims = decode_token_unverified(token)
    return claims.get("role", "")


def get_token_user_id(token: str) -> str:
    """Extract the user_id claim from a JWT."""
    claims = decode_token_unverified(token)
    return claims.get("user_id", "")


def get_token_tenant_ids(token: str) -> list[str]:
    """Extract tenant_ids from a JWT."""
    claims = decode_token_unverified(token)
    return claims.get("tenant_ids", [])


def is_token_expired(token: str) -> bool:
    """Check if a JWT's exp claim is in the past."""
    claims = decode_token_unverified(token)
    exp = claims.get("exp", 0)
    return time.time() > exp


def build_tampered_token(
    original_token: str,
    claim_overrides: dict[str, Any],
) -> str:
    """Build a tampered JWT by modifying claims without valid signature.

    Returns a token signed with a fake key — should be rejected by the API.
    """
    claims = decode_token_unverified(original_token)
    claims.update(claim_overrides)
    return jwt.encode(claims, "fake-secret-key", algorithm="HS256")


def build_none_alg_token(original_token: str) -> str:
    """Build a JWT with alg=none (should be rejected by the API)."""
    claims = decode_token_unverified(original_token)
    # Manually build a token with alg=none
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps(claims).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}."


def build_expired_token(original_token: str) -> str:
    """Build a JWT with exp set to a past timestamp."""
    return build_tampered_token(original_token, {"exp": int(time.time()) - 3600})
