from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CurrentPlanView, PlanPaymentViewSet, PlanViewSet, SettingsView

router = DefaultRouter()
router.register("payments", PlanPaymentViewSet, basename="plan-payment")
router.register("tiers", PlanViewSet, basename="plan")

urlpatterns = [
    path("current/", CurrentPlanView.as_view(), name="plan-current"),
    path("settings/", SettingsView.as_view(), name="plan-settings"),
    path("", include(router.urls)),
]
