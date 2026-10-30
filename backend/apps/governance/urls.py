from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, MeetingViewSet, PollViewSet

router = DefaultRouter()
router.register("polls", PollViewSet, basename="poll")
router.register("meetings", MeetingViewSet, basename="meeting")
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = [path("", include(router.urls))]
