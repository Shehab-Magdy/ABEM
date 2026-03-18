"""User create/teardown fixtures."""

from __future__ import annotations

import logging

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_admin_user, build_owner_user

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def create_user(admin_api: APIRequestContext):
    """Factory fixture: create users and clean up on teardown."""
    created_ids: list[str] = []

    def _create(role: str = "owner", **overrides) -> dict:
        if role == "admin":
            payload = build_admin_user(**overrides)
        else:
            payload = build_owner_user(**overrides)
        resp = admin_api.post("/api/v1/users/", data=payload)
        assert resp.status == 201, f"Create user failed: {resp.text()}"
        data = resp.json()
        created_ids.append(data["id"])
        data["_password"] = payload["password"]
        logger.info("Created user %s (%s, role=%s)", data["id"], data.get("email"), role)
        return data

    yield _create

    for uid in reversed(created_ids):
        resp = admin_api.delete(f"/api/v1/users/{uid}/")
        logger.debug("Deleted user %s (status=%s)", uid, resp.status)


@pytest.fixture(scope="function")
def temp_owner(create_user):
    """Create a temporary owner user and return their data."""
    return create_user(role="owner")


@pytest.fixture(scope="function")
def temp_admin(create_user):
    """Create a temporary admin user and return their data."""
    return create_user(role="admin")
