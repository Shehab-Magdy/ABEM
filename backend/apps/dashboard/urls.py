from django.urls import path

from .views import AdminDashboardView, OwnerDashboardView

urlpatterns = [
    path("admin/", AdminDashboardView.as_view(), name="dashboard-admin"),
    path("owner/", OwnerDashboardView.as_view(), name="dashboard-owner"),
]
