"""Dashboard aggregation views — Sprint 5."""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils.translation import gettext_lazy as _
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
                    {"detail": _("Building not found or not accessible by you.")},
                    status=403,
                )
            buildings = buildings.filter(pk=building_id)

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        today = date.today()

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

        # ── Month-over-month % change (always current vs previous month) ──────
        first_of_this_month = today.replace(day=1)
        prev_month_date = first_of_this_month - timedelta(days=1)
        prev_year, prev_month = prev_month_date.year, prev_month_date.month

        curr_month_income = (
            Payment.objects.filter(
                apartment__building__in=buildings,
                payment_date__year=today.year,
                payment_date__month=today.month,
            ).aggregate(s=Sum("amount_paid"))["s"] or Decimal("0.00")
        )
        prev_month_income = (
            Payment.objects.filter(
                apartment__building__in=buildings,
                payment_date__year=prev_year,
                payment_date__month=prev_month,
            ).aggregate(s=Sum("amount_paid"))["s"] or Decimal("0.00")
        )
        income_change_pct = (
            round(float((curr_month_income - prev_month_income) / prev_month_income * 100), 1)
            if prev_month_income > 0 else None
        )

        curr_month_expense = (
            Expense.objects.filter(
                building__in=buildings,
                expense_date__year=today.year,
                expense_date__month=today.month,
                deleted_at__isnull=True,
            ).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
        )
        prev_month_expense = (
            Expense.objects.filter(
                building__in=buildings,
                expense_date__year=prev_year,
                expense_date__month=prev_month,
                deleted_at__isnull=True,
            ).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
        )
        expense_change_pct = (
            round(float((curr_month_expense - prev_month_expense) / prev_month_expense * 100), 1)
            if prev_month_expense > 0 else None
        )

        # ── Overdue count (balance > 0) ───────────────────────────────────────
        overdue_count = (
            Apartment.objects.filter(building__in=buildings, balance__gt=0).count()
        )

        # ── Overdue units (balance > 0 AND has a past-due expense) ───────────
        from apps.expenses.models import ApartmentExpense
        overdue_units_count = (
            Apartment.objects.filter(
                building__in=buildings,
                balance__gt=0,
                apartment_expenses__expense__due_date__lt=today,
                apartment_expenses__expense__deleted_at__isnull=True,
            ).distinct().count()
        )

        # ── Monthly trend (12 months of current year) ─────────────────────────
        monthly_trend = []
        for month_num in range(1, 13):
            m_income = (
                Payment.objects.filter(
                    apartment__building__in=buildings,
                    payment_date__year=today.year,
                    payment_date__month=month_num,
                ).aggregate(s=Sum("amount_paid"))["s"]
                or Decimal("0.00")
            )
            m_expenses = (
                Expense.objects.filter(
                    building__in=buildings,
                    expense_date__year=today.year,
                    expense_date__month=month_num,
                    deleted_at__isnull=True,
                ).aggregate(s=Sum("amount"))["s"]
                or Decimal("0.00")
            )
            monthly_trend.append({
                "month": f"{today.year}-{month_num:02d}",
                "income": str(m_income),
                "expenses": str(m_expenses),
            })

        # ── Building summary ──────────────────────────────────────────────────
        all_apts = Apartment.objects.filter(building__in=buildings)
        building_summary = {
            "total_buildings": buildings.count(),
            "total_units": all_apts.count(),
            "occupied": all_apts.filter(status="occupied").count(),
            "vacant": all_apts.filter(status="vacant").count(),
        }

        # ── Payment collection progress ───────────────────────────────────────
        billed_apt_ids = list(
            ApartmentExpense.objects.filter(
                expense__building__in=buildings,
                expense__deleted_at__isnull=True,
            ).values_list("apartment_id", flat=True).distinct()
        )
        total_billed = len(billed_apt_ids)
        paid_count = Apartment.objects.filter(
            id__in=billed_apt_ids, balance__lte=0
        ).count()
        payment_coverage = {
            "total_billed": total_billed,
            "paid": paid_count,
        }

        # ── Unpaid units table ────────────────────────────────────────────────
        unpaid_units = list(
            Apartment.objects.filter(building__in=buildings, balance__gt=0)
            .select_related("building")
            .order_by("-balance")
            .values(
                "unit_number",
                "balance",
                "building__name",
                "owner__first_name",
                "owner__last_name",
                "owner__email",
            )[:50]
        )
        unpaid_rows = [
            {
                "unit_number": r["unit_number"],
                "balance": str(r["balance"]),
                "building_name": r["building__name"] or "",
                "owner_name": (
                    f"{r['owner__first_name'] or ''} {r['owner__last_name'] or ''}".strip()
                    or r["owner__email"] or "—"
                ),
                "owner_email": r["owner__email"] or "",
            }
            for r in unpaid_units
        ]

        # ── Recent expenses (last 30 days) ────────────────────────────────────
        thirty_days_ago = today - timedelta(days=30)
        recent_exp_qs = (
            Expense.objects.filter(
                building__in=buildings,
                deleted_at__isnull=True,
                expense_date__gte=thirty_days_ago,
            )
            .select_related("category")
            .order_by("-expense_date")[:20]
        )
        recent_expenses = [
            {
                "title": e.title,
                "category": e.category.name if e.category else "Uncategorized",
                "amount": str(e.amount),
                "status": str(_("Overdue")) if (e.due_date and e.due_date < today) else str(_("Active")),
            }
            for e in recent_exp_qs
        ]

        return Response({
            "total_income":        str(total_income),
            "income_change_pct":   income_change_pct,
            "total_expenses":      str(total_expenses),
            "expense_change_pct":  expense_change_pct,
            "overdue_count":       overdue_count,
            "overdue_units_count": overdue_units_count,
            "monthly_trend":       monthly_trend,
            "building_summary":    building_summary,
            "payment_coverage":    payment_coverage,
            "unpaid_units":        unpaid_rows,
            "recent_expenses":     recent_expenses,
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
        from django.db.models import Q
        apartments = Apartment.objects.filter(
            Q(owner=request.user) | Q(owners=request.user)
        ).distinct()

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
