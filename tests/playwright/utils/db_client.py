"""psycopg2 helper utilities for direct database assertions.

Every function takes a psycopg2 connection as the first argument
so that tests can pass the fixture-managed connection with rollback.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import psycopg2
import psycopg2.extras


def get_connection(dsn: str) -> psycopg2.extensions.connection:
    """Open a new psycopg2 connection with RealDictCursor."""
    conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False
    return conn


def query_one(
    conn: psycopg2.extensions.connection,
    sql: str,
    params: tuple | dict | None = None,
) -> dict[str, Any] | None:
    """Execute SQL and return a single row as dict, or None."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def query_all(
    conn: psycopg2.extensions.connection,
    sql: str,
    params: tuple | dict | None = None,
) -> list[dict[str, Any]]:
    """Execute SQL and return all rows as list of dicts."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def query_scalar(
    conn: psycopg2.extensions.connection,
    sql: str,
    params: tuple | dict | None = None,
) -> Any:
    """Execute SQL and return the first column of the first row."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None


def count(
    conn: psycopg2.extensions.connection,
    table: str,
    where: str = "1=1",
    params: tuple | dict | None = None,
) -> int:
    """Return the row count for a table with optional WHERE clause."""
    sql = f"SELECT COUNT(*) FROM {table} WHERE {where}"  # noqa: S608
    return query_scalar(conn, sql, params) or 0


def column_type(
    conn: psycopg2.extensions.connection,
    table: str,
    column: str,
) -> str:
    """Return the PostgreSQL data type of a column."""
    sql = """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """
    return query_scalar(conn, sql, (table, column)) or ""


def row_exists(
    conn: psycopg2.extensions.connection,
    table: str,
    where: str,
    params: tuple | dict | None = None,
) -> bool:
    """Return True if at least one row matches."""
    sql = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {where})"  # noqa: S608
    return query_scalar(conn, sql, params) is True


def get_audit_logs(
    conn: psycopg2.extensions.connection,
    *,
    entity: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """Query the audit_logs table with optional filters."""
    clauses = ["1=1"]
    params: list[Any] = []

    # Try both table names
    table = "audit_logs"
    try:
        query_one(conn, f"SELECT 1 FROM {table} LIMIT 1")
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        table = "audit_auditlog"

    if entity:
        clauses.append("entity = %s")
        params.append(entity)
    if entity_id:
        clauses.append("entity_id::text = %s")
        params.append(str(entity_id))
    if action:
        clauses.append("action = %s")
        params.append(action)
    if user_id:
        clauses.append("user_id::text = %s")
        params.append(str(user_id))

    sql = f"SELECT * FROM {table} WHERE {' AND '.join(clauses)} ORDER BY created_at DESC"  # noqa: S608
    return query_all(conn, sql, tuple(params))


def get_apartment_expenses(
    conn: psycopg2.extensions.connection,
    expense_id: str,
) -> list[dict[str, Any]]:
    """Return all apartment_expense rows for a given expense."""
    # Try Django table naming convention
    table = "expenses_apartmentexpense"
    try:
        query_one(conn, f"SELECT 1 FROM {table} LIMIT 0")
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        table = "apartment_expenses"

    sql = f"SELECT * FROM {table} WHERE expense_id::text = %s"  # noqa: S608
    return query_all(conn, sql, (str(expense_id),))


def get_notifications_for_user(
    conn: psycopg2.extensions.connection,
    user_id: str,
    *,
    notification_type: str | None = None,
) -> list[dict[str, Any]]:
    """Return notification rows for a user, optionally filtered by type."""
    table = "notifications_notification"
    try:
        query_one(conn, f"SELECT 1 FROM {table} LIMIT 0")
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        table = "notifications"

    clauses = ["user_id::text = %s"]
    params: list[Any] = [str(user_id)]
    if notification_type:
        clauses.append("notification_type = %s")
        params.append(notification_type)

    sql = f"SELECT * FROM {table} WHERE {' AND '.join(clauses)} ORDER BY created_at DESC"  # noqa: S608
    return query_all(conn, sql, tuple(params))


def get_decimal(value: Any) -> Decimal:
    """Safely convert a DB value to Python Decimal."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
