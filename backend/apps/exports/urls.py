"""URL patterns for the exports app."""
from django.urls import path

from .views import ExportAssetSalesView, ExportBuildingView, ExportExpensesView, ExportPaymentsView

urlpatterns = [
    path("payments/", ExportPaymentsView.as_view(), name="export-payments"),
    path("expenses/", ExportExpensesView.as_view(), name="export-expenses"),
    path("asset-sales/", ExportAssetSalesView.as_view(), name="export-asset-sales"),
    path("building/<uuid:building_id>/", ExportBuildingView.as_view(), name="export-building"),
]
