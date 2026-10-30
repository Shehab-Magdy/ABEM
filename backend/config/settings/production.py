"""
ABEM – Production settings.
"""
from .base import *  # noqa: F401, F403
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from decouple import Csv, config

DEBUG = False

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

# Host names only (no scheme). Override with DJANGO_ALLOWED_HOSTS if the host changes.
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="3mara.com,www.3mara.com", cast=Csv())

# TLS is terminated by the proxy (nginx / hosting platform); trust its forwarded scheme
# so SECURE_SSL_REDIRECT does not loop.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# MIDDLEWARE is inherited from base.py (it already includes security, whitenoise, CORS and language).

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS", default="https://3mara.com,https://www.3mara.com", cast=Csv()
)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS", default="https://3mara.com,https://www.3mara.com", cast=Csv()
)
# Vercel preview deployments of the frontend
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://abem-.*\.vercel\.app$",
]
