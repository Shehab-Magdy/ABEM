"""Full single-building XLSX export: units, residents, expenses, payments, claims, late fees, audit log."""

from __future__ import annotations

import io

import openpyxl
from apps.apartments.models import Apartment
from apps.audit.models import AuditLog
from apps.expenses.models import Expense, LateFee
from apps.exports.safe import safe_row
from apps.payments.models import Payment, PaymentClaim
from apps.plans.models import PlanPayment
from django.db.models import Q


def _text(value) -> str:
    return "" if value is None else str(value)


def _units(building):
    rows = [
        [
            "Unit",
            "Floor",
            "Type",
            "Size (sqm)",
            "Status",
            "Rate factor",
            "Balance",
            "Billing paused",
        ]
    ]
    for a in Apartment.objects.filter(building=building).order_by("unit_number"):
        rows.append(
            [
                a.unit_number,
                a.floor,
                a.unit_type,
                _text(a.size_sqm),
                a.status,
                _text(a.rate_factor),
                _text(a.balance),
                "yes" if a.billing_paused else "no",
            ]
        )
    return rows


def _residents(building):
    rows = [["Unit", "Role", "Name", "Email", "Phone", "Primary owner"]]
    qs = Apartment.objects.filter(building=building).prefetch_related("owners").select_related("owner")
    for a in qs.order_by("unit_number"):
        people = {u.pk: u for u in a.owners.all()}
        if a.owner_id and a.owner_id not in people:
            people[a.owner_id] = a.owner
        for u in people.values():
            rows.append(
                [
                    a.unit_number,
                    u.role,
                    f"{u.first_name} {u.last_name}".strip(),
                    u.email,
                    _text(u.phone),
                    "yes" if u.pk == a.owner_id else "no",
                ]
            )
    return rows


def _expenses(building):
    rows = [
        [
            "ID",
            "Title",
            "Category",
            "Kind",
            "Amount",
            "Expense date",
            "Due date",
            "Split type",
            "Approval",
            "Deleted",
        ]
    ]
    qs = Expense.objects.filter(building=building).select_related("category").order_by("-expense_date")
    for e in qs:
        rows.append(
            [
                str(e.id),
                e.title,
                e.category.name if e.category_id else "",
                e.kind,
                _text(e.amount),
                _text(e.expense_date),
                _text(e.due_date),
                e.split_type,
                e.approval_status,
                "yes" if e.deleted_at else "no",
            ]
        )
    return rows


def _payments(building):
    rows = [
        [
            "ID",
            "Receipt no",
            "Unit",
            "Amount",
            "Method",
            "Date",
            "Balance before",
            "Balance after",
            "Reversal of",
            "Reversal reason",
            "Notes",
        ]
    ]
    qs = Payment.objects.filter(apartment__building=building).select_related("apartment").order_by("-payment_date")
    for p in qs:
        rows.append(
            [
                str(p.id),
                _text(p.receipt_no),
                p.apartment.unit_number,
                _text(p.amount_paid),
                p.payment_method,
                _text(p.payment_date),
                _text(p.balance_before),
                _text(p.balance_after),
                _text(p.reversal_of_id),
                p.reversal_reason,
                p.notes,
            ]
        )
    return rows


def _claims(building):
    rows = [
        [
            "ID",
            "Unit",
            "Amount",
            "Reference",
            "Status",
            "Created",
            "Reviewed",
            "Payment",
            "Payment reversed",
        ]
    ]
    reversed_ids = set(
        Payment.objects.filter(apartment__building=building, reversal_of__isnull=False).values_list(
            "reversal_of_id", flat=True
        )
    )
    qs = PaymentClaim.objects.filter(apartment__building=building).select_related("apartment")
    for c in qs.order_by("-created_at"):
        rows.append(
            [
                str(c.id),
                c.apartment.unit_number,
                _text(c.amount),
                c.reference,
                c.status,
                _text(c.created_at),
                _text(c.reviewed_at),
                _text(c.payment_id),
                "yes" if c.payment_id and c.payment_id in reversed_ids else "no",
            ]
        )
    return rows


def _late_fees(building):
    rows = [["ID", "Unit", "Expense", "Amount", "Created", "Waived at", "Waived reason"]]
    qs = LateFee.objects.filter(expense__building=building).select_related("expense", "share__apartment")
    for f in qs.order_by("-created_at"):
        rows.append(
            [
                str(f.id),
                f.share.apartment.unit_number,
                f.expense.title,
                _text(f.expense.amount),
                _text(f.created_at),
                _text(f.waived_at),
                f.waived_reason,
            ]
        )
    return rows


def _audit(building):
    rows = [["When", "User", "Action", "Entity", "Entity ID", "Changes"]]
    unit_ids = Apartment.objects.filter(building=building).values("id")
    expense_ids = Expense.objects.filter(building=building).values("id")
    payment_ids = Payment.objects.filter(apartment__building=building).values("id")
    claim_ids = PaymentClaim.objects.filter(apartment__building=building).values("id")
    plan_payment_ids = PlanPayment.objects.filter(building=building).values("id")
    qs = (
        AuditLog.objects.filter(
            Q(entity_id=building.pk)
            | Q(entity_id__in=unit_ids)
            | Q(entity_id__in=expense_ids)
            | Q(entity_id__in=payment_ids)
            | Q(entity_id__in=claim_ids)
            | Q(entity_id__in=plan_payment_ids)
            | Q(changes__building_id=str(building.pk))
        )
        .select_related("user")
        .order_by("-created_at")
    )
    for log in qs:
        rows.append(
            [
                _text(log.created_at),
                log.user.email if log.user_id else "",
                log.action,
                log.entity,
                _text(log.entity_id),
                _text(log.changes),
            ]
        )
    return rows


SHEETS = (
    ("Units", _units),
    ("Residents", _residents),
    ("Expenses", _expenses),
    ("Payments", _payments),
    ("Claims", _claims),
    ("Late fees", _late_fees),
    ("Audit log", _audit),
)


def build_workbook(building) -> bytes:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for title, rows_fn in SHEETS:
        ws = wb.create_sheet(title)
        for row in rows_fn(building):
            ws.append(safe_row(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
