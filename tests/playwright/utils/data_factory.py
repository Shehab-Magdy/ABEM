"""Faker-based test data builders for ABEM resources.

Every builder returns a plain dict suitable for POST request bodies.
"""

from __future__ import annotations

import random
import string
from datetime import date, timedelta
from uuid import uuid4

from faker import Faker

fake = Faker()


def unique_prefix() -> str:
    """Short unique prefix for test data names."""
    return f"test_{uuid4().hex[:8]}"


def unique_email() -> str:
    """Unique email address for test users."""
    return f"{unique_prefix()}@abem.test"


# ── Users ─────────────────────────────────────────────────────


def build_admin_user(**overrides: object) -> dict:
    """Build a payload for creating an admin user."""
    data = {
        "email": unique_email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "phone": fake.phone_number()[:20],
        "role": "admin",
        "password": "Test@1234!",
    }
    data.update(overrides)
    return data


def build_owner_user(**overrides: object) -> dict:
    """Build a payload for creating an owner user."""
    data = build_admin_user(role="owner", **overrides)
    return data


# ── Buildings ─────────────────────────────────────────────────


def build_building(**overrides: object) -> dict:
    """Build a payload for creating a building."""
    prefix = unique_prefix()
    data = {
        "name": f"{prefix} Building",
        "address": fake.address().replace("\n", ", "),
        "city": fake.city(),
        "country": "Egypt",
        "num_floors": random.randint(3, 10),
        "num_apartments": 2,
        "num_stores": 1,
    }
    data.update(overrides)
    return data


# ── Apartments ────────────────────────────────────────────────


def build_apartment(building_id: str, **overrides: object) -> dict:
    """Build a payload for creating an apartment."""
    data = {
        "building_id": building_id,
        "unit_number": f"U-{uuid4().hex[:6].upper()}",
        "floor": random.randint(1, 5),
        "type": "apartment",
        "size_sqm": str(random.randint(50, 200)),
        "status": "vacant",
    }
    data.update(overrides)
    return data


def build_store(building_id: str, **overrides: object) -> dict:
    """Build a payload for creating a store unit."""
    return build_apartment(building_id, type="store", **overrides)


# ── Expenses ──────────────────────────────────────────────────


def build_expense(building_id: str, category_id: str, **overrides: object) -> dict:
    """Build a payload for creating an expense."""
    data = {
        "building_id": building_id,
        "category_id": category_id,
        "title": f"{unique_prefix()} Expense",
        "description": fake.sentence(),
        "amount": str(random.randint(100, 5000)),
        "expense_date": date.today().isoformat(),
        "split_type": "equal_all",
        "is_recurring": False,
    }
    data.update(overrides)
    return data


def build_recurring_expense(
    building_id: str,
    category_id: str,
    **overrides: object,
) -> dict:
    """Build a recurring expense payload."""
    data = build_expense(
        building_id,
        category_id,
        is_recurring=True,
        frequency="monthly",
        **overrides,
    )
    return data


# ── Payments ──────────────────────────────────────────────────


def build_payment(apartment_id: str, **overrides: object) -> dict:
    """Build a payload for recording a payment."""
    data = {
        "apartment_id": apartment_id,
        "amount_paid": str(random.randint(50, 500)),
        "payment_method": random.choice(["cash", "bank_transfer", "cheque"]),
        "payment_date": date.today().isoformat(),
        "notes": fake.sentence(),
    }
    data.update(overrides)
    return data


# ── Categories ────────────────────────────────────────────────


def build_category(building_id: str, **overrides: object) -> dict:
    """Build a payload for creating an expense category."""
    data = {
        "building_id": building_id,
        "name": f"{unique_prefix()} Category",
        "description": fake.sentence(),
        "icon": "category",
        "color": f"#{fake.hex_color().lstrip('#')[:6]}",
    }
    data.update(overrides)
    return data


# ── Notifications ─────────────────────────────────────────────


def build_broadcast(building_id: str, **overrides: object) -> dict:
    """Build a payload for admin broadcast notification."""
    data = {
        "subject": f"{unique_prefix()} Broadcast",
        "message": fake.paragraph(),
        "building_id": building_id,
    }
    data.update(overrides)
    return data


# ── Security payloads ────────────────────────────────────────


SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    "1; SELECT * FROM users--",
    "' UNION SELECT null, email, password_hash FROM users--",
    "admin'--",
    "1' OR '1' = '1' /*",
]

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    '<img src=x onerror="alert(1)">',
    "javascript:alert(1)",
    '<svg onload="alert(1)">',
    "'\"><script>alert(document.cookie)</script>",
]

HEADER_INJECTION_PAYLOADS = [
    "value\r\nX-Injected: true",
    "value\nX-Injected: true",
    "value%0d%0aX-Injected:%20true",
]


def generate_password(
    length: int = 12,
    uppercase: bool = True,
    digit: bool = True,
    special: bool = True,
) -> str:
    """Generate a password meeting complexity requirements."""
    chars = list(string.ascii_lowercase[:length - 3])
    if uppercase:
        chars.append(random.choice(string.ascii_uppercase))
    if digit:
        chars.append(random.choice(string.digits))
    if special:
        chars.append(random.choice("!@#$%^&*"))
    while len(chars) < length:
        chars.append(random.choice(string.ascii_lowercase))
    random.shuffle(chars)
    return "".join(chars)
