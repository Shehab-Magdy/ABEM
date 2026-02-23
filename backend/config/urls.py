"""ABEM URL Configuration."""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Health check
    path("api/health/", include("apps.core.urls")),

    # API v1
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/users/", include("apps.authentication.user_urls")),
    path("api/v1/buildings/", include("apps.buildings.urls")),
    path("api/v1/apartments/", include("apps.apartments.urls")),
    path("api/v1/expenses/", include("apps.expenses.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),

    # OpenAPI docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
