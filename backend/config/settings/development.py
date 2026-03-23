"""
ABEM – Development settings.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

# Insert debug toolbar after GZip so Django doesn't warn about ordering
MIDDLEWARE.insert(  # noqa: F405
    MIDDLEWARE.index("django.middleware.gzip.GZipMiddleware") + 1,  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)

INTERNAL_IPS = ["127.0.0.1"]

# Use console email backend in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relaxed CORS for local dev
CORS_ALLOW_ALL_ORIGINS = True

# Disable SSL requirement for local postgres
DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}  # noqa: F405

# Use local filesystem storage in development (avoids Cloudinary dependency)
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405
