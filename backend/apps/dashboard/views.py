"""Dashboard aggregation views — Sprint 5."""
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsAdminRole
from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import Expense
from apps.payments.models import Payment


class AdminDashboardView(APIView):
    """
    GET /api/v1/dashboard/admin/

    Returns building-wide financial dashboard aggregations.
    Scoped to buildings administered by the requesting admin.

    Query Params:
        building_id  — optional; scope to a single building (must be administered by user)
        date_from    — optional ISO date; filter payments/expenses from this date
        date_to      — optional ISO date; filter payments/expenses up to this date
    """

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        from django.db.models import Q as DQ
        # Buildings this admin created, is co-admin of, or is a member of
        buildings = Building.objects.filter(
            DQ(admin=request.user) | DQ(co_admins=request.user) | DQ(members=request.user),
            deleted_at__isnull=True,
        ).distinct()

        building_id = request.query_params.get("building_id")
        if building_id:
            if not buildings.filter(pk=building_id).exists():
                return Response(
                    {"detail": "Building not found or not accessible by you."},
                    status=403,
                )
            buildings = buildings.filter(pk=building_id)

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        # ── Totals ────────────────────────────────────────────────────────────
        payment_qs = Payment.objects.filter(apartment__building__in=buildings)
        if date_from:
            payment_qs = payment_qs.filter(payment_date__gte=date_from)
        if date_to:
            payment_qs = payment_qs.filter(payment_date__lte=date_to)
        total_income = payment_qs.aggregate(s=Sum("amount_paid"))["s"] or Decimal("0.00")

        expense_qs = Expense.objects.filter(building__in=buildings, deleted_at__isnull=True)
        if date_from:
            expense_qs = expense_qs.filter(expense_date__gte=date_from)
        if date_to:
            expense_qs = expense_qs.filter(expense_date__lte=date_to)
        total_expenses = expense_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")

        # ── Overdue count ─────────────────────────────────────────────────────
        overdue_count = (
            Apartment.objects.filter(building__in=buildings, balance__gt=0).count()
        )

        # ── Monthly trend (12 months of current year) ─────────────────────────
        current_year = date.today().year
        monthly_trend = []
        for month_num in range(1, 13):
            m_income = (
                Payment.objects.filter(
                    apartment__building__in=buildings,
                    payment_date__year=current_year,
                    payment_date__month=month_num,
                ).aggregate(s=Sum("amount_paid"))["s"]
                or Decimal("0.00")
            )
            m_expenses = (
                Expense.objects.filter(
                    building__in=buildings,
                    expense_date__year=current_year,
                    expense_date__month=month_num,
                    deleted_at__isnull=True,
                ).aggregate(s=Sum("amount"))["s"]
                or Decimal("0.00")
            )
            monthly_trend.append({
                "month": f"{current_year}-{month_num:02d}",
                "income": str(m_income),
                "expenses": str(m_expenses),
            })

        # ── Building summary ──────────────────────────────────────────────────
        all_apts = Apartment.objects.filter(building__in=buildings)
        building_summary = {
            "total_buildings": buildings.count(),
            "total_apartments": all_apts.count(),
            "occupied": all_apts.filter(status="occupied").count(),
            "vacant": all_apts.filter(status="vacant").count(),
        }

        return Response({
            "total_income":     str(total_income),
            "total_expenses":   str(total_expenses),
            "overdue_count":    overdue_count,
            "monthly_trend":    monthly_trend,
            "building_summary": building_summary,
        })


class OwnerDashboardView(APIView):
    """
    GET /api/v1/dashboard/owner/

    Returns owner-specific financial dashboard.
    Scoped to apartments owned by the requesting user.

    Query Params:
        date_from    — optional ISO date
        date_to      — optional ISO date
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        apartments = Apartment.objects.filter(owner=request.user)

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        # ── Balance summary ───────────────────────────────────────────────────
        current_balance = (
            apartments.aggregate(s=Sum("balance"))["s"] or Decimal("0.00")
        )
        ytd_qs = Payment.objects.filter(
            apartment__in=apartments,
            payment_date__year=date.today().year,
        )
        total_paid_ytd = ytd_qs.aggregate(s=Sum("amount_paid"))["s"] or Decimal("0.00")

        # ── Recent payments (last 5) ──────────────────────────────────────────
        payment_filter = {"apartment__in": apartments}
        if date_from:
            payment_filter["payment_date__gte"] = date_from
        if date_to:
            payment_filter["payment_date__lte"] = date_to

        recent_qs = (
            Payment.objects.filter(**payment_filter)
            .order_by("-payment_date", "-created_at")[:5]
        )
        recent_payments = [
            {
                "id": str(p.pk),
                "apartment_id": str(p.apartment_id),
                "amount_paid": str(p.amount_paid),
                "payment_method": p.payment_method,
                "payment_date": str(p.payment_date),
                "notes": p.notes or "",
            }
            for p in recent_qs
        ]

        # ── Expense breakdown by category ──────────────────────────────────
        from apps.expenses.models import ApartmentExpense

        breakdown_qs = (
            ApartmentExpense.objects.filter(
                apartment__in=apartments,
                expense__deleted_at__isnull=True,
            )
        )
        if date_from:
            breakdown_qs = breakdown_qs.filter(expense__expense_date__gte=date_from)
        if date_to:
            breakdown_qs = breakdown_qs.filter(expense__expense_date__lte=date_to)

        breakdown_qs = (
            breakdown_qs
            .values("expense__category__name")
            .annotate(total=Sum("share_amount"))
            .order_by("-total")
        )
        expense_breakdown = [
            {
                "category_name": row["expense__category__name"] or "Uncategorized",
                "total": str(row["total"]),
            }
            for row in breakdown_qs
        ]

        return Response({
            "balance_summary": {
                "current_balance": str(current_balance),
                "total_paid_ytd":  str(total_paid_ytd),
            },
            "recent_payments":   recent_payments,
            "expense_breakdown": expense_breakdown,
        })
