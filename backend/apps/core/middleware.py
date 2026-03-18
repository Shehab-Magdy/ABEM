"""SEO-related middleware for the ABEM API."""


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
