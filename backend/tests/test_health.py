from unittest import mock

import pytest
from rest_framework.test import APIClient

from apps.core.views import HealthCheckView

URL = "/api/health/"


@pytest.mark.django_db
def test_health_ok_when_dependencies_up():
    res = APIClient().get(URL)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert set(res.json()["checks"]) == {"database", "cache", "migrations"}


@pytest.mark.django_db
def test_health_503_when_database_down():
    broken = mock.Mock(side_effect=Exception("boom"))
    with mock.patch.dict(HealthCheckView.checks, {"database": broken}):
        res = APIClient().get(URL)
    assert res.status_code == 503
    body = res.json()
    assert body["status"] == "unavailable"
    assert body["checks"]["database"] == "error"
    assert "boom" not in res.content.decode()
