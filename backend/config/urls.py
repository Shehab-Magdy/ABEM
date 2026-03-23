"""ABEM URL Configuration."""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.core.views import sitemap_xml

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Rosetta translation management (staff only)
    path("rosetta/", include("rosetta.urls")),

    # SEO — sitemap fallback (served by web server in production)
    path("sitemap.xml", sitemap_xml, name="sitemap"),

    # Health check
    path("api/health/", include("apps.core.urls")),

    # API v1
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/users/", include("apps.authentication.user_urls")),
    path("api/v1/buildings/", include("apps.buildings.urls")),
    path("api/v1/apartments/", include("apps.apartments.urls")),
    path("api/v1/expenses/", include("apps.expenses.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/exports/", include("apps.exports.urls")),

    # OpenAPI docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

    # Serve uploaded media files locally in development
    from django.conf.urls.static import static
    urlpatterns += static(
        settings.MEDIA_URL, document_root=getattr(settings, "MEDIA_ROOT", "")
    )
