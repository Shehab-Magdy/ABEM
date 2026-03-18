"""Custom assertpy extensions and assertion helpers for ABEM tests."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from assertpy import assert_that


# ── Decimal assertions ────────────────────────────────────────


def assert_decimal_equal(actual: Any, expected: str | Decimal) -> None:
    """Assert two values are equal as Decimal — never use float."""
    actual_d = Decimal(str(actual))
    expected_d = Decimal(str(expected))
    assert actual_d == expected_d, (
        f"Decimal mismatch: actual={actual_d} expected={expected_d}"
    )


def assert_decimal_gte(actual: Any, minimum: str | Decimal) -> None:
    """Assert actual >= minimum as Decimal."""
    actual_d = Decimal(str(actual))
    min_d = Decimal(str(minimum))
    assert actual_d >= min_d, (
        f"Decimal {actual_d} is less than minimum {min_d}"
    )


def assert_decimal_positive(value: Any) -> None:
    """Assert a Decimal value is > 0."""
    d = Decimal(str(value))
    assert d > Decimal("0"), f"Expected positive Decimal, got {d}"


# ── API response assertions ──────────────────────────────────


def assert_status(response: Any, expected: int) -> None:
    """Assert HTTP response status code."""
    assert response.status == expected, (
        f"Expected status {expected}, got {response.status}: {response.text()}"
    )


def assert_status_in(response: Any, codes: list[int]) -> None:
    """Assert HTTP response status is one of the expected codes."""
    assert response.status in codes, (
        f"Expected one of {codes}, got {response.status}: {response.text()}"
    )


def assert_json_has_keys(data: dict, *keys: str) -> None:
    """Assert a JSON dict contains all specified keys."""
    missing = [k for k in keys if k not in data]
    assert not missing, f"Missing keys in response: {missing}"


def assert_json_field_equals(data: dict, field: str, expected: Any) -> None:
    """Assert a specific JSON field value."""
    assert field in data, f"Field '{field}' not in response"
    assert data[field] == expected, (
        f"Field '{field}': expected {expected!r}, got {data[field]!r}"
    )


def assert_error_field_mentioned(response_json: dict, field: str) -> None:
    """Assert that a validation error response mentions a specific field."""
    text = str(response_json).lower()
    assert field.lower() in text, (
        f"Expected field '{field}' mentioned in error response: {response_json}"
    )


def assert_no_sensitive_fields(data: dict) -> None:
    """Assert that response body does not contain password-related fields."""
    forbidden = {"password", "password_hash", "password1", "password2"}
    found = forbidden & set(data.keys())
    assert not found, f"Sensitive fields exposed in response: {found}"


def assert_list_response(data: dict) -> None:
    """Assert standard paginated list response structure."""
    assert_json_has_keys(data, "count", "results")
    assert isinstance(data["results"], list)


# ── Split calculation assertions ──────────────────────────────


def assert_shares_sum_gte_amount(shares: list[dict], total_amount: str | Decimal) -> None:
    """Assert the sum of share_amount values >= the original expense amount."""
    total = sum(Decimal(str(s["share_amount"])) for s in shares)
    expected = Decimal(str(total_amount))
    assert total >= expected, (
        f"Sum of shares ({total}) is less than expense amount ({expected})"
    )


def assert_round_up_to_5(value: Any) -> None:
    """Assert a value is a multiple of 5."""
    d = Decimal(str(value))
    assert d % 5 == 0, f"Value {d} is not rounded to nearest 5"


# ── PDF assertions ────────────────────────────────────────────


def assert_valid_pdf(content: bytes) -> None:
    """Assert content starts with PDF magic bytes."""
    assert content[:5] == b"%PDF-", "Content is not a valid PDF (missing %PDF- header)"


# ── UUID assertion ────────────────────────────────────────────


def assert_valid_uuid(value: str) -> None:
    """Assert a string is a valid UUID format."""
    import re
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    assert re.match(pattern, str(value), re.IGNORECASE), (
        f"Not a valid UUID: {value}"
    )
