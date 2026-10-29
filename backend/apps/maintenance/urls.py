from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MaintenanceReportViewSet

router = DefaultRouter()
router.register("", MaintenanceReportViewSet, basename="maintenance-report")

urlpatterns = [path("", include(router.urls))]
