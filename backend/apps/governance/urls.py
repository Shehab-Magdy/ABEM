from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PollViewSet

router = DefaultRouter()
router.register("polls", PollViewSet, basename="poll")

urlpatterns = [path("", include(router.urls))]
