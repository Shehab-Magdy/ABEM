"""
Test data factories for the ABEM automation framework.

Uses Faker to generate realistic, unique data for each test run.
All generated emails contain '@abem.test' to clearly identify them as test data.

Usage:
    from utils.test_data import UserFactory, PasswordFactory, TokenFactory

    user = UserFactory.admin()
    user = UserFactory.owner()
    bad_pw = PasswordFactory.weak()
"""

from __future__ import annotations

import random
import string
import uuid
from typing import Optional

from faker import Faker

fake = Faker()


class UserFactory:
    """Generate user payloads compatible with the ABEM /auth/register/ API."""

    @staticmethod
    def _unique_email(prefix: str) -> str:
        uid = str(uuid.uuid4())[:8]
        return f"{prefix}_{uid}@abem.test"

    @staticmethod
    def admin(
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> dict:
        """Valid admin user payload (passes all backend validators)."""
        return {
            "email": email or UserFactory._unique_email("admin"),
            "password": password or "Admin@1234",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "role": "admin",
            "phone": fake.numerify("+20##########"),
        }

    @staticmethod
    def owner(
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> dict:
        """Valid owner user payload."""
        return {
            "email": email or UserFactory._unique_email("owner"),
            "password": password or "Owner@1234",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "role": "owner",
            "phone": fake.numerify("+20##########"),
        }

    @staticmethod
    def invalid_emails() -> list[str]:
        """List of email strings that should fail backend/frontend validation."""
        return [
            "",                       # empty
            "notanemail",             # missing @
            "missing@",               # no domain
            "@nodomain.com",          # no local part
            "double@@domain.com",     # double @
            "space in@email.com",     # space
            "a" * 255 + "@abem.test", # too long
        ]

    @staticmethod
    def update_payload() -> dict:
        """Valid PATCH /auth/profile/ payload."""
        return {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone": fake.numerify("+20##########"),
        }


class PasswordFactory:
    """Generate passwords for testing the complexity validator."""

    VALID = "Secure@2024"

    @staticmethod
    def valid() -> str:
        return PasswordFactory.VALID

    @staticmethod
    def weak_samples() -> list[dict]:
        """
        Returns list of dicts with 'password' and 'reason' keys.
        Each password should be rejected by PasswordComplexityValidator.
        """
        return [
            {"password": "short1A!",      "reason": "too short (< 8 chars)"},
            {"password": "alllowercase1!", "reason": "no uppercase letter"},
            {"password": "ALLUPPERCASE1!", "reason": "no lowercase letter"},
            {"password": "NoDigitsHere!",  "reason": "no digit"},
            {"password": "NoSpecial123",   "reason": "no special character"},
            {"password": "password",       "reason": "common word, no complexity"},
            {"password": "12345678",       "reason": "digits only"},
        ]

    @staticmethod
    def new_valid(exclude: Optional[str] = None) -> str:
        """Generate a unique valid password different from `exclude`."""
        candidates = ["NewPass@2024", "Fresh@Pass1", "Change#Me99", "Secure!2025"]
        for c in candidates:
            if c != exclude:
                return c
        return f"P@ss{random.randint(1000, 9999)}!"


class TokenFactory:
    """Generate token strings for negative auth tests."""

    @staticmethod
    def invalid_access_token() -> str:
        """A syntactically plausible but cryptographically invalid JWT."""
        return (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiJ0ZXN0IiwiaWF0IjoxNjAwMDAwMDAwfQ"
            ".INVALID_SIGNATURE_HERE"
        )

    @staticmethod
    def random_string(length: int = 64) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def expired_token() -> str:
        """
        A real-looking JWT with exp set in the past.
        The backend will reject it on verification.
        """
        # Header: {"alg":"HS256","typ":"JWT"}
        # Payload: {"token_type":"refresh","exp":1000000000,"user_id":"test"}
        return (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTAwMDAwMDAwMCwidXNlcl9pZCI6InRlc3QifQ"
            ".fake_sig"
        )


class BuildingFactory:
    """Payloads for Building API tests (Sprint 2+)."""

    @staticmethod
    def valid() -> dict:
        return {
            "name": f"{fake.last_name()} Building",
            "address": fake.address().replace("\n", ", "),
            "city": fake.city(),
            "floors": random.randint(3, 20),
            "units_per_floor": random.randint(2, 8),
        }
