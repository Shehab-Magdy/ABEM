"""Cookie names/paths and set/clear helpers for refresh + trusted-device cookies."""
from django.conf import settings

REFRESH_COOKIE_NAME = "refresh_token"
# Scoped to the whole auth namespace (not just /refresh/) so it's also sent to
# /auth/logout/ and any other auth endpoint that needs to read it. HttpOnly +
# SameSite=Lax are the real security boundary here, not the cookie path.
REFRESH_COOKIE_PATH = "/api/v1/auth/"

TRUSTED_DEVICE_COOKIE_NAME = "trusted_device"
TRUSTED_DEVICE_COOKIE_PATH = "/api/v1/auth/otp/request/"


def set_refresh_cookie(response, refresh_token: str, max_age: int = None):
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=max_age,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


def set_trusted_device_cookie(response, device_token: str, max_age: int):
    response.set_cookie(
        TRUSTED_DEVICE_COOKIE_NAME,
        device_token,
        max_age=max_age,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path=TRUSTED_DEVICE_COOKIE_PATH,
    )


def clear_trusted_device_cookie(response):
    response.delete_cookie(TRUSTED_DEVICE_COOKIE_NAME, path=TRUSTED_DEVICE_COOKIE_PATH)
