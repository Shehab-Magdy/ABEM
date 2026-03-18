"""Database connection fixtures using psycopg2."""

from __future__ import annotations

import logging

import psycopg2
import psycopg2.extras
import pytest

from config.settings import settings

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def db_conn():
    """Function-scoped psycopg2 connection with rollback after each test.

    Auto-commit is OFF. The connection rolls back after each test
    to prevent state leakage from direct DB writes.
    """
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    conn.autocommit = False
    logger.debug("Opened DB connection for test")

    yield conn

    conn.rollback()
    conn.close()
    logger.debug("Rolled back and closed DB connection")


@pytest.fixture(scope="session")
def db_conn_session():
    """Session-scoped DB connection for read-only assertions.

    Does not roll back — use only for SELECTs, never for writes.
    """
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    conn.autocommit = True
    logger.info("Opened session-scoped DB connection")

    yield conn

    conn.close()
    logger.info("Closed session-scoped DB connection")
