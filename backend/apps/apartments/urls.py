from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApartmentViewSet, UnitClaimRequestViewSet

router = DefaultRouter()
router.register("claim-requests", UnitClaimRequestViewSet, basename="unit-claim-request")
router.register("", ApartmentViewSet, basename="apartment")

urlpatterns = [path("", include(router.urls))]
