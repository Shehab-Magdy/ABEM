from pathlib import Path

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "service": "ABEM API"})


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
    <loc>https://abem.app/</loc>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://abem.app/login</loc>
    <changefreq>yearly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://abem.app/register</loc>
    <changefreq>yearly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>"""
    return HttpResponse(xml, content_type="application/xml")
