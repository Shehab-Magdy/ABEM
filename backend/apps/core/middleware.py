"""SEO and i18n middleware for the ABEM API."""
from django.conf import settings
from django.utils import translation


class APIRobotsMiddleware:
    """Add X-Robots-Tag: noindex to all /api/ responses.

    Prevents search engines from indexing any API endpoint, including
    /api/health/, /api/v1/*, /api/docs/, /api/schema/, etc.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/"):
            response["X-Robots-Tag"] = "noindex"
        return response


class APILanguageMiddleware:
    """Activate the language from Accept-Language for all API requests.

    Ensures server-side rendered strings in API responses (validation
    errors, choice labels, etc.) are returned in the requested language.
    Falls back to settings.LANGUAGE_CODE ("en") for unsupported languages.
    """

    SUPPORTED = None  # lazily populated

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            if self.SUPPORTED is None:
                self.SUPPORTED = {code for code, _ in settings.LANGUAGES}
            accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
            lang = accept.split(",")[0].split(";")[0].strip()[:2].lower()
            if lang not in self.SUPPORTED:
                lang = settings.LANGUAGE_CODE
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        return response


class StaticCacheControlMiddleware:
    """Add aggressive Cache-Control headers for static assets.

    Targets /static/ paths served by WhiteNoise in production.
    Immutable assets (hashed filenames from Vite/WhiteNoise) get 1 year
    cache with the immutable directive.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/static/"):
            response["Cache-Control"] = "public, max-age=31536000, immutable"
        return response
