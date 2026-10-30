from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContractorViewSet, ObligationViewSet

router = DefaultRouter()
router.register("contractors", ContractorViewSet, basename="contractor")
router.register("obligations", ObligationViewSet, basename="obligation")

urlpatterns = [path("", include(router.urls))]
