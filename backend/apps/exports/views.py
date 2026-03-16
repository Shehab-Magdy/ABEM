"""CSV / XLSX export views for payments and expenses – Sprint 8."""
from __future__ import annotations

import csv
import io

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.authentication.permissions import IsAdminRole
from apps.expenses.models import Expense
from apps.payments.models import Payment


class ExportPaymentsView(APIView):
    """
    GET /api/v1/exports/payments/

    Export all payment records in CSV or XLSX format.

    Query params:
      - format      csv (default) | xlsx
      - apartment_id  UUID — filter by apartment
      - date_from     ISO date — inclusive lower bound on payment_date
      - date_to       ISO date — inclusive upper bound on payment_date
    """

    permission_classes = [IsAuthenticated, IsAdminRole]

    _HEADERS = ["ID", "Apartment", "Amount", "Method", "Date", "Balance Before", "Balance After"]

    def get(self, request):
        qs = Payment.objects.select_related("apartment").order_by("-payment_date", "-created_at")
        p = request.query_params

        if apt_id := p.get("apartment_id"):
            qs = qs.filter(apartment_id=apt_id)
        if d_from := p.get("date_from"):
            qs = qs.filter(payment_date__gte=d_from)
        if d_to := p.get("date_to"):
            qs = qs.filter(payment_date__lte=d_to)

        return self._csv_response(qs)

    def _rows(self, qs):
        for pay in qs:
            yield [
                str(pay.id),
                str(pay.apartment),
                str(pay.amount_paid),
                pay.payment_method,
                str(pay.payment_date),
                str(pay.balance_before),
                str(pay.balance_after),
            ]

    def _csv_response(self, qs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="payments.csv"'
        writer = csv.writer(response)
        writer.writerow(self._HEADERS)
        for row in self._rows(qs):
            writer.writerow(row)
        return response


class ExportExpensesView(APIView):
    """
    GET /api/v1/exports/expenses/

    Export expense records in CSV or XLSX format.

    Query params:
      - format      csv (default) | xlsx
      - building_id   UUID — filter by building
      - date_from     ISO date — inclusive lower bound on expense_date
      - date_to       ISO date — inclusive upper bound on expense_date
    """

    permission_classes = [IsAuthenticated, IsAdminRole]

    _HEADERS = ["ID", "Building", "Category", "Title", "Amount", "Date", "Split Type"]

    def get(self, request):
        qs = (
            Expense.objects.filter(deleted_at__isnull=True)
            .select_related("building", "category")
            .order_by("-expense_date")
        )
        p = request.query_params

        if bld_id := p.get("building_id"):
            qs = qs.filter(building_id=bld_id)
        if d_from := p.get("date_from"):
            qs = qs.filter(expense_date__gte=d_from)
        if d_to := p.get("date_to"):
            qs = qs.filter(expense_date__lte=d_to)

        fmt = (p.get("file_format") or "csv").lower()

        if fmt == "xlsx":
            return self._xlsx_response(qs)
        return self._csv_response(qs)

    def _rows(self, qs):
        for exp in qs:
            yield [
                str(exp.id),
                str(exp.building),
                str(exp.category.name),
                exp.title,
                str(exp.amount),
                str(exp.expense_date),
                exp.split_type,
            ]

    def _csv_response(self, qs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="expenses.csv"'
        writer = csv.writer(response)
        writer.writerow(self._HEADERS)
        for row in self._rows(qs):
            writer.writerow(row)
        return response

    def _xlsx_response(self, qs):
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Expenses"
        ws.append(self._HEADERS)
        for row in self._rows(qs):
            ws.append(row)

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        response = HttpResponse(
            buf.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="expenses.xlsx"'
        return response
