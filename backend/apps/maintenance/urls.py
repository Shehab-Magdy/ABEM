from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MaintenanceReportViewSet, WorkOrderViewSet

router = DefaultRouter()
router.register("work-orders", WorkOrderViewSet, basename="work-order")
router.register("", MaintenanceReportViewSet, basename="maintenance-report")

urlpatterns = [path("", include(router.urls))]
