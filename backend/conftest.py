"""Root pytest configuration and shared fixtures."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@abem.test",
        password="AdminPass1!",
        first_name="Admin",
        last_name="User",
        role="admin",
    )


@pytest.fixture
def owner_user(db):
    return User.objects.create_user(
        email="owner@abem.test",
        password="OwnerPass1!",
        first_name="Owner",
        last_name="User",
        role="owner",
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client


@pytest.fixture
def owner_client(api_client, owner_user):
    refresh = RefreshToken.for_user(owner_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client
