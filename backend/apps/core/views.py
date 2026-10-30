import logging
from pathlib import Path

from django.core.cache import cache
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


def _check_database():
    with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()


def _check_cache():
    cache.set("health-check", "ok", 5)
    if cache.get("health-check") != "ok":
        raise RuntimeError("cache read-back mismatch")


def _check_migrations():
    connection = connections[DEFAULT_DB_ALIAS]
    executor = MigrationExecutor(connection)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise RuntimeError("unapplied migrations")


class HealthCheckView(APIView):
    """Liveness plus dependency readiness: 200 only if every check passes, else 503.

    Failure details go to the log, not the response, because the endpoint is public.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    checks = {
        "database": _check_database,
        "cache": _check_cache,
        "migrations": _check_migrations,
    }

    def get(self, request):
        results = {}
        for name, check in self.checks.items():
            try:
                check()
                results[name] = "ok"
            except Exception:
                logger.warning("Health check failed: %s", name, exc_info=True)
                results[name] = "error"
        healthy = all(v == "ok" for v in results.values())
        return Response(
            {
                "status": "ok" if healthy else "unavailable",
                "service": "3maracom API",
                "checks": results,
            },
            status=200 if healthy else 503,
        )


_SITEMAP_FILENAME = "sitemap.xml"


def sitemap_xml(_request):
    """Serve sitemap.xml as a fallback when not handled by the web server.

    Reads the sitemap from the Vite build output (frontend/public/sitemap.xml)
    or returns a minimal inline version if the file is not found.
    """
    # Try to find the sitemap in the frontend dist or public directory
    base = Path(__file__).resolve().parent.parent.parent
    for candidate in [
        base / "staticfiles" / _SITEMAP_FILENAME,
        base.parent / "frontend" / "public" / _SITEMAP_FILENAME,
        base.parent / "frontend" / "dist" / _SITEMAP_FILENAME,
    ]:
        if candidate.is_file():
            return HttpResponse(
                candidate.read_text(encoding="utf-8"),
                content_type="application/xml",
            )

    # Inline fallback
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://3mara.com/</loc>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://3mara.com/login</loc>
    <changefreq>yearly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://3mara.com/register</loc>
    <changefreq>yearly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>"""
    return HttpResponse(xml, content_type="application/xml")
