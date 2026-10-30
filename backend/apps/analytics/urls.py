from django.urls import path

from .views import PlatformKpisView

urlpatterns = [path("platform/", PlatformKpisView.as_view(), name="analytics-platform")]
