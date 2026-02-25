"""URL patterns for the exports app."""
from django.urls import path

from .views import ExportExpensesView, ExportPaymentsView

urlpatterns = [
    path("payments/", ExportPaymentsView.as_view(), name="export-payments"),
    path("expenses/", ExportExpensesView.as_view(), name="export-expenses"),
]
