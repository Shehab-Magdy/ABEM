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
            {"password": "Sh@1",           "reason": "too short (< 8 chars)"},
            {"password": "alllower1!",     "reason": "no uppercase letter"},
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
    """Payloads for Building API tests (Sprint 2)."""

    @staticmethod
    def valid(num_floors: int | None = None) -> dict:
        """Valid building creation payload matching POST /buildings/ contract."""
        return {
            "name": f"{fake.last_name()} Building",
            "address": fake.address().replace("\n", ", "),
            "city": fake.city(),
            "country": fake.country(),
            "num_floors": num_floors if num_floors is not None else random.randint(3, 20),
            "num_apartments": random.randint(2, 8),
        }

    @staticmethod
    def missing_name() -> dict:
        d = BuildingFactory.valid()
        d.pop("name")
        return d

    @staticmethod
    def missing_address() -> dict:
        d = BuildingFactory.valid()
        d.pop("address")
        return d

    @staticmethod
    def zero_floors() -> dict:
        d = BuildingFactory.valid()
        d["num_floors"] = 0
        return d

    @staticmethod
    def negative_apartments() -> dict:
        d = BuildingFactory.valid()
        d["num_apartments"] = -1
        return d


class ApartmentFactory:
    """Payloads for Apartment API tests (Sprint 2)."""

    @staticmethod
    def valid(building_id: str, num_floors: int = 10) -> dict:
        """Valid apartment creation payload matching POST /apartments/ contract."""
        floor = random.randint(1, num_floors)
        uid = str(uuid.uuid4())[:6]
        return {
            "building_id": building_id,
            "unit_number": f"{floor}{uid}",
            "floor": floor,
            "unit_type": "apartment",
            "size_sqm": round(random.uniform(50.0, 200.0), 2),
            "status": "vacant",
        }

    @staticmethod
    def store(building_id: str, num_floors: int = 10) -> dict:
        """Valid store-type apartment payload."""
        d = ApartmentFactory.valid(building_id, num_floors)
        d["unit_type"] = "store"
        return d

    @staticmethod
    def invalid_type(building_id: str) -> dict:
        d = ApartmentFactory.valid(building_id)
        d["unit_type"] = "InvalidType"
        return d

    @staticmethod
    def floor_exceeds_max(building_id: str, num_floors: int) -> dict:
        d = ApartmentFactory.valid(building_id, num_floors)
        d["floor"] = num_floors + 1
        return d


class CategoryFactory:
    """Payloads for ExpenseCategory API tests (Sprint 3)."""

    @staticmethod
    def valid(building_id: str, name: Optional[str] = None) -> dict:
        """Valid category creation payload."""
        uid = str(uuid.uuid4())[:6]
        return {
            "building_id": building_id,
            "name": name or f"Category-{uid}",
            "description": fake.sentence(nb_words=6),
        }

    @staticmethod
    def missing_building() -> dict:
        """Payload without building_id — triggers 400."""
        return {"name": f"Cat-{str(uuid.uuid4())[:6]}"}

    @staticmethod
    def missing_name(building_id: str) -> dict:
        d = CategoryFactory.valid(building_id)
        d.pop("name")
        return d


class ExpenseFactory:
    """Payloads for Expense API tests (Sprint 3)."""

    @staticmethod
    def valid(building_id: str, category_id: str, amount: float = 100.0) -> dict:
        """Valid expense creation payload."""
        return {
            "building_id": building_id,
            "category_id": category_id,
            "title": fake.sentence(nb_words=4).rstrip("."),
            "description": fake.sentence(nb_words=8),
            "amount": str(round(amount, 2)),
            "expense_date": fake.date_between(start_date="-30d", end_date="today").isoformat(),
            "split_type": "equal_all",
        }

    @staticmethod
    def recurring(building_id: str, category_id: str) -> dict:
        """Expense payload with is_recurring=True and monthly frequency."""
        d = ExpenseFactory.valid(building_id, category_id)
        d["is_recurring"] = True
        d["frequency"] = "monthly"
        return d

    @staticmethod
    def zero_amount(building_id: str, category_id: str) -> dict:
        d = ExpenseFactory.valid(building_id, category_id)
        d["amount"] = "0.00"
        return d

    @staticmethod
    def negative_amount(building_id: str, category_id: str) -> dict:
        d = ExpenseFactory.valid(building_id, category_id)
        d["amount"] = "-50.00"
        return d

    @staticmethod
    def missing_category(building_id: str) -> dict:
        """Payload without category_id — triggers 400."""
        return {
            "building_id": building_id,
            "title": "No Category",
            "amount": "100.00",
            "expense_date": "2026-01-01",
            "split_type": "equal_all",
        }

    @staticmethod
    def missing_date(building_id: str, category_id: str) -> dict:
        d = ExpenseFactory.valid(building_id, category_id)
        d.pop("expense_date")
        return d

    @staticmethod
    def future_date(building_id: str, category_id: str) -> dict:
        """Future expense date — valid per the SRS."""
        d = ExpenseFactory.valid(building_id, category_id)
        d["expense_date"] = fake.date_between(
            start_date="+1d", end_date="+30d"
        ).isoformat()
        return d

    @staticmethod
    def custom_split(building_id: str, category_id: str, apartment_ids: list) -> dict:
        d = ExpenseFactory.valid(building_id, category_id)
        d["split_type"] = "custom"
        d["custom_split_apartments"] = apartment_ids
        return d
