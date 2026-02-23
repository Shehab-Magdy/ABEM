"""
ABEM – Development settings.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]

# Use console email backend in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relaxed CORS for local dev
CORS_ALLOW_ALL_ORIGINS = True

# Disable SSL requirement for local postgres
DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}  # noqa: F405
