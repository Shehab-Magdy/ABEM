from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BuildingAssetViewSet, PaymentViewSet

router = DefaultRouter()
router.register("assets", BuildingAssetViewSet, basename="asset")
router.register("", PaymentViewSet, basename="payment")

urlpatterns = [path("", include(router.urls))]
