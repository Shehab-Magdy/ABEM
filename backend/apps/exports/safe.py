"""Neutralise spreadsheet formula injection in user-controlled cells."""

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value):
    """Prefix strings that a spreadsheet would treat as a formula with a single quote; others are untouched."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def safe_row(row):
    return [safe_cell(v) for v in row]
