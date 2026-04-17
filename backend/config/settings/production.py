"""
ABEM – Production settings.
"""
from .base import *  # noqa: F401, F403
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from decouple import config
import dj_database_url

DEBUG = False

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", cast=lambda v: v.split(",") if v else [])

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default=config("POSTGRES_URL", default="")),
    )
}

# These headers are required when Django is behind Render's HTTPS and proxy layer.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host]

# Security hardening
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"


# Content Security Policy
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Sentry error tracking
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
