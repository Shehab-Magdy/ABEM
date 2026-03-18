"""Helpers for parsing and validating CSV and XLSX export data."""

from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any


def parse_csv_bytes(content: bytes) -> list[dict[str, str]]:
    """Parse CSV bytes into a list of dicts keyed by header names."""
    text = content.decode("utf-8-sig")  # handle BOM
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def parse_csv_text(text: str) -> list[dict[str, str]]:
    """Parse CSV text into a list of dicts."""
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def get_csv_headers(content: bytes) -> list[str]:
    """Extract header names from CSV content."""
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    return next(reader, [])


def validate_csv_row_count(content: bytes, expected_count: int) -> None:
    """Assert the CSV has exactly expected_count data rows (excluding header)."""
    rows = parse_csv_bytes(content)
    assert len(rows) == expected_count, (
        f"Expected {expected_count} CSV rows, got {len(rows)}"
    )


def validate_csv_has_columns(content: bytes, columns: list[str]) -> None:
    """Assert the CSV header contains all specified column names."""
    headers = get_csv_headers(content)
    normalized_headers = [h.strip().lower() for h in headers]
    for col in columns:
        assert col.strip().lower() in normalized_headers, (
            f"Column '{col}' not found in CSV headers: {headers}"
        )


def parse_xlsx_bytes(content: bytes) -> list[dict[str, Any]]:
    """Parse XLSX bytes into a list of dicts keyed by header names.

    Requires openpyxl.
    """
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h) if h else f"col_{i}" for i, h in enumerate(rows[0])]
    return [dict(zip(headers, row)) for row in rows[1:]]


def get_xlsx_row_count(content: bytes) -> int:
    """Return the number of data rows in the first sheet (excluding header)."""
    rows = parse_xlsx_bytes(content)
    return len(rows)


def compare_csv_to_api(
    csv_rows: list[dict[str, str]],
    api_records: list[dict[str, Any]],
    key_field: str,
    compare_fields: list[str],
) -> list[str]:
    """Compare CSV export data against API response records.

    Returns a list of mismatch descriptions (empty = all match).
    """
    mismatches: list[str] = []

    api_by_key = {str(r.get(key_field, "")): r for r in api_records}

    for csv_row in csv_rows:
        csv_key = csv_row.get(key_field, "").strip()
        if csv_key not in api_by_key:
            mismatches.append(f"CSV row key '{csv_key}' not found in API data")
            continue
        api_row = api_by_key[csv_key]
        for field in compare_fields:
            csv_val = csv_row.get(field, "").strip()
            api_val = str(api_row.get(field, "")).strip()
            if csv_val != api_val:
                mismatches.append(
                    f"Key={csv_key} field={field}: CSV='{csv_val}' API='{api_val}'"
                )

    return mismatches
