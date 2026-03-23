"""Payment views – Sprint 4 + Sprint 8 (PDF receipt) + BF-01 (i18n/RTL)."""
from __future__ import annotations

import html as html_lib

from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db import transaction

from django.utils.translation import gettext_lazy as _
from apps.apartments.models import Apartment
from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole

from .models import AssetSale, BuildingAsset, Payment, PaymentExpense, PaymentMethod
from .serializers import BuildingAssetSerializer, PaymentSerializer


# ── Arabic numeral / receipt helpers ─────────────────────────────────────────

_EASTERN_ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩'


def _to_eastern_arabic(value: str) -> str:
    """Replace ASCII digits with Eastern Arabic-Indic digits."""
    return ''.join(
        _EASTERN_ARABIC_DIGITS[int(ch)] if ch.isdigit() else ch
        for ch in str(value)
    )


def _fmt_money(amount, lang: str) -> str:
    """Format a Decimal/float as a money string with currency label."""
    formatted = f"{amount:,.2f}"
    currency = "ج.م" if lang == "ar" else "EGP"
    if lang == "ar":
        return f"{_to_eastern_arabic(formatted)} {currency}"
    return f"{formatted} {currency}"


# Labels used in the receipt, keyed by language code
_RECEIPT_LABELS = {
    "en": {
        "receipt_title": "PAYMENT RECEIPT",
        "receipt_no": "Receipt No",
        "building": "BUILDING",
        "unit": "UNIT",
        "owner": "OWNER",
        "amount_paid": "Amount Paid",
        "payment_date": "Payment Date",
        "payment_method": "Payment Method",
        "for_expenses": "For Expenses",
        "balance_before": "Balance Before",
        "balance_after": "Balance After",
        "recorded_by": "Recorded By",
        "notes": "Notes",
        "general_payment": "General payment",
        "paid_received": "PAID {amount} RECEIVED",
        "footer": "This is an automatically generated receipt. ABEM - abem.app",
        "subtitle": "Apartment & Building Expense Management",
        # payment method translations
        "cash": "Cash",
        "bank_transfer": "Bank Transfer",
        "cheque": "Cheque",
        "mobile_wallet": "Mobile Wallet",
        "other": "Other",
    },
    "ar": {
        "receipt_title": "إيصال دفع",
        "receipt_no": "رقم الإيصال",
        "building": "المبنى",
        "unit": "الوحدة",
        "owner": "المالك",
        "amount_paid": "المبلغ المدفوع",
        "payment_date": "تاريخ الدفع",
        "payment_method": "طريقة الدفع",
        "for_expenses": "للمصروفات",
        "balance_before": "الرصيد قبل",
        "balance_after": "الرصيد بعد",
        "recorded_by": "سُجّل بواسطة",
        "notes": "ملاحظات",
        "general_payment": "دفعة عامة",
        "paid_received": "تم الدفع {amount} تم الاستلام",
        "footer": "هذا إيصال تم إنشاؤه تلقائيا. app.abem - ABEM",
        "subtitle": "إدارة مصروفات الشقق والمباني",
        # payment method translations
        "cash": "نقداً",
        "bank_transfer": "تحويل بنكي",
        "cheque": "شيك",
        "mobile_wallet": "محفظة موبايل",
        "other": "أخرى",
    },
}


class PaymentViewSet(ModelViewSet):
    """
    Payment management with atomic balance updates.

    Payments are IMMUTABLE after creation (no PATCH or DELETE).

    Permissions:
      - Admin:  POST (record) + GET all.
      - Owner:  GET only (own apartments).
      - Unauthenticated: 401.
    """

    serializer_class = PaymentSerializer

    # No PUT / PATCH / DELETE — payments are an immutable ledger
    http_method_names = ["get", "post", "options", "head"]

    # ── Scoping & filtering ─────────────────────────────────────────────────────

    def get_queryset(self):
        qs = Payment.objects.select_related("apartment", "recorded_by").prefetch_related(
            "expenses", "payment_expenses", "payment_expenses__expense",
        )

        if self.request.user.role != "admin":
            # Owners see payments for any apartment they are primary or co-owner of
            from django.db.models import Q
            qs = qs.filter(
                Q(apartment__owner=self.request.user) | Q(apartment__owners=self.request.user)
            ).distinct()

        params = self.request.query_params
        apt_id     = params.get("apartment_id")
        date_from  = params.get("date_from")
        date_to    = params.get("date_to")
        method     = params.get("payment_method")

        if apt_id:    qs = qs.filter(apartment_id=apt_id)
        if date_from: qs = qs.filter(payment_date__gte=date_from)
        if date_to:   qs = qs.filter(payment_date__lte=date_to)
        if method:    qs = qs.filter(payment_method=method)

        return qs

    # ── Permissions ─────────────────────────────────────────────────────────────

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    # ── Write helper ────────────────────────────────────────────────────────────

    def perform_create(self, serializer):
        """
        Atomically:
          1. Lock the apartment row (select_for_update).
          2. Snapshot balance_before.
          3. Deduct amount_paid from apartment.balance.
          4. Save Payment with balance snapshots + recorded_by.
          5. Create PaymentExpense rows with optional allocations.
          6. Emit audit log.
        """
        from decimal import Decimal

        apartment = serializer.validated_data["apartment"]
        amount_paid = serializer.validated_data["amount_paid"]
        raw_allocations = self.request.data.get("allocations", [])

        with transaction.atomic():
            apt = Apartment.objects.select_for_update().get(pk=apartment.pk)
            balance_before = apt.balance
            apt.balance -= amount_paid
            apt.save(update_fields=["balance", "updated_at"])

            payment = serializer.save(
                recorded_by=self.request.user,
                balance_before=balance_before,
                balance_after=apt.balance,
            )

            # Handle manual allocations if provided
            if raw_allocations:
                for alloc in raw_allocations:
                    expense_id = alloc.get("expense_id")
                    alloc_amount = alloc.get("allocated_amount")
                    PaymentExpense.objects.update_or_create(
                        payment=payment,
                        expense_id=expense_id,
                        defaults={
                            "allocated_amount": Decimal(str(alloc_amount)) if alloc_amount is not None else None,
                        },
                    )

        # Determine audit action based on whether allocations were distributed
        audit_action = "payment.distributed" if raw_allocations else "create"
        log_action(
            user=self.request.user,
            action=audit_action,
            entity="payment",
            entity_id=payment.pk,
            request=self.request,
        )
        try:
            from apps.notifications.services import notify_payment_confirmed
            notify_payment_confirmed(payment)
        except Exception:
            pass

    # ── PDF Receipt ──────────────────────────────────────────────────────────────

    @action(
        detail=True,
        methods=["get"],
        url_path="receipt",
        permission_classes=[IsAuthenticated],
    )
    def receipt(self, request, pk=None):
        """
        GET /api/v1/payments/{id}/receipt/

        Returns a formatted PDF receipt. Admin sees any payment; owners see
        only payments for their own apartments.
        Uses WeasyPrint (HTML → PDF) so Arabic and all Unicode text renders correctly.
        """
        from weasyprint import HTML

        payment = self.get_object()

        # Owners may only view receipts for their own apartments
        apt = payment.apartment
        if request.user.role != "admin":
            is_owner = (apt.owner == request.user) or apt.owners.filter(pk=request.user.pk).exists()
            if not is_owner:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(_("You do not have permission to view this receipt."))

        # Determine language from user preference
        lang = getattr(request.user, "preferred_language", None) or "en"
        labels = _RECEIPT_LABELS.get(lang, _RECEIPT_LABELS["en"])
        is_rtl = lang == "ar"

        def esc(value) -> str:
            """HTML-escape any user-provided value to prevent injection in the PDF."""
            return html_lib.escape(str(value))

        linked_expenses = list(payment.expenses.all())
        expense_str = (
            ", ".join(esc(e.title) for e in linked_expenses)
            if linked_expenses
            else labels["general_payment"]
        )

        recorded_by_name = (
            esc(payment.recorded_by.get_full_name() or payment.recorded_by.email)
            if payment.recorded_by else "—"
        )

        # Translate payment method using the labels dict
        method_display = labels.get(payment.payment_method, payment.payment_method.replace("_", " ").title())

        fields = [
            (labels["amount_paid"],    _fmt_money(payment.amount_paid, lang)),
            (labels["payment_date"],   _to_eastern_arabic(str(payment.payment_date)) if is_rtl else str(payment.payment_date)),
            (labels["payment_method"], method_display),
            (labels["for_expenses"],   expense_str),
            (labels["balance_before"], _fmt_money(payment.balance_before, lang)),
            (labels["balance_after"],  _fmt_money(payment.balance_after, lang)),
            (labels["recorded_by"],    recorded_by_name),
            (labels["notes"],          esc(payment.notes or "—")),
        ]
        if is_rtl:
            rows_html = "".join(
                f'<tr><td class="val">{value}</td><td class="lbl">{label}</td></tr>'
                for label, value in fields
            )
        else:
            rows_html = "".join(
                f'<tr><td class="lbl">{label}</td><td class="val">{value}</td></tr>'
                for label, value in fields
            )

        # Owner display — prefer primary owner, fall back to first M2M owner
        if apt.owner:
            owner_display = esc(apt.owner.get_full_name() or apt.owner.email)
        else:
            first_owner = apt.owners.first()
            owner_display = esc(first_owner.get_full_name() or first_owner.email) if first_owner else "—"

        receipt_no_label = labels["receipt_no"]
        receipt_no_value = str(payment.id)[:8].upper()
        if is_rtl:
            receipt_no_value = _to_eastern_arabic(receipt_no_value)
        paid_amount_display = _fmt_money(payment.amount_paid, lang)
        paid_received_text = labels["paid_received"].replace("{amount}", paid_amount_display)

        html_dir = "rtl" if is_rtl else "ltr"
        lbl_align = "right" if is_rtl else "left"
        val_align = "left" if is_rtl else "right"
        html_content = f"""<!DOCTYPE html>
<html dir="{html_dir}" lang="{lang}">
<head>
<meta charset="utf-8">
<style>
  @import url("https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&family=Noto+Sans+Arabic:wght@400;700&display=swap");
  @page {{ size: A6; margin: 0; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Noto Sans Arabic", "Noto Sans", "Segoe UI", Tahoma, Arial, sans-serif;
    font-size: 8pt;
    color: #222;
    position: relative;
    width: 105mm;
    min-height: 148mm;
    direction: {html_dir};
  }}
  .header {{
    background: #1E3A5F;
    color: white;
    padding: 5mm 8mm;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .logo {{ font-size: 14pt; font-weight: bold; }}
  .subtitle {{ font-size: 7pt; margin-top: 2px; }}
  .receipt-title {{ font-size: 10pt; font-weight: bold; text-align: {val_align}; }}
  .receipt-no {{ font-size: 7pt; text-align: {val_align}; margin-top: 2px; }}
  .info-section {{
    background: #F0F4F8;
    margin: 3mm 6mm 0;
    padding: 3mm 5mm;
    display: flex;
    justify-content: space-between;
  }}
  .info-label {{ color: #1E3A5F; font-size: 6.5pt; font-weight: bold; margin-bottom: 1px; }}
  .info-value {{ font-size: 8pt; unicode-bidi: plaintext; }}
  .details-table {{
    width: calc(100% - 12mm);
    margin: 3mm 6mm 0;
    border-collapse: collapse;
  }}
  .details-table tr {{ height: 7mm; }}
  .details-table tr:nth-child(odd) td {{ background: #F0F4F8; }}
  .details-table td {{ padding: 1.5mm 3mm; vertical-align: middle; }}
  .details-table td.lbl {{ color: #555; font-size: 7pt; font-weight: bold; width: 38%; text-align: {lbl_align}; }}
  .details-table td.val {{ font-size: 7.5pt; text-align: {val_align}; unicode-bidi: plaintext; }}
  .paid-box {{
    background: #E8F5E9;
    color: #2E7D32;
    font-size: 9pt;
    font-weight: bold;
    text-align: center;
    margin: 3mm 6mm 0;
    padding: 2.5mm;
    border-radius: 2mm;
  }}
  .footer {{
    position: absolute;
    bottom: 4mm;
    width: 100%;
    text-align: center;
    color: #888;
    font-size: 6pt;
  }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <div class="logo">ABEM</div>
      <div class="subtitle">{labels["subtitle"]}</div>
    </div>
    <div>
      <div class="receipt-title">{labels["receipt_title"]}</div>
      <div class="receipt-no">{receipt_no_label}: {receipt_no_value}</div>
    </div>
  </div>

  <div class="info-section">
    <div>
      <div class="info-label">{labels["building"]}</div>
      <div class="info-value">{esc(apt.building.name)}</div>
    </div>
    <div>
      <div class="info-label">{labels["unit"]}</div>
      <div class="info-value">{esc(apt.unit_number)} | {esc(apt.get_unit_type_display())}</div>
    </div>
    <div>
      <div class="info-label">{labels["owner"]}</div>
      <div class="info-value">{owner_display}</div>
    </div>
  </div>

  <table class="details-table">
    {rows_html}
  </table>

  <div class="paid-box">&#10003; {paid_received_text}</div>

  <div class="footer">{labels["footer"]}</div>
</body>
</html>"""

        try:
            pdf_bytes = HTML(string=html_content).write_pdf()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error("WeasyPrint PDF generation failed: %s", exc, exc_info=True)
            return Response(
                {"detail": f"PDF generation failed: {exc}. Ensure WeasyPrint and its system libraries are installed (rebuild the Docker container if needed)."},
                status=503,
            )

        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="receipt_{str(payment.id)[:8]}.pdf"'
        return resp


class BuildingAssetViewSet(ModelViewSet):
    """
    CRUD for building assets + sell action.

    GET    /payments/assets/?building_id=  – list
    POST   /payments/assets/               – create
    PATCH  /payments/assets/{id}/          – update
    POST   /payments/assets/{id}/sell/     – record a sale
    """

    serializer_class = BuildingAssetSerializer
    http_method_names = ["get", "post", "patch", "options", "head"]
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        qs = BuildingAsset.objects.select_related("building", "sale")
        building_id = self.request.query_params.get("building_id")
        if building_id:
            qs = qs.filter(building_id=building_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="sell")
    def sell(self, request, pk=None):
        """
        POST /api/v1/payments/assets/{id}/sell/
        Body: {sale_date, sale_price, buyer_name, buyer_contact, notes}
        Marks the asset as sold and records the sale.
        """
        asset = self.get_object()
        if asset.is_sold:
            return Response({"detail": _("This asset has already been sold.")}, status=400)

        sale_date = request.data.get("sale_date")
        sale_price = request.data.get("sale_price")
        if not sale_date or sale_price is None:
            return Response({"detail": _("sale_date and sale_price are required.")}, status=400)

        with transaction.atomic():
            AssetSale.objects.create(
                asset=asset,
                sale_date=sale_date,
                sale_price=sale_price,
                buyer_name=request.data.get("buyer_name", ""),
                buyer_contact=request.data.get("buyer_contact", ""),
                notes=request.data.get("notes", ""),
                recorded_by=request.user,
            )
            asset.is_sold = True
            asset.save(update_fields=["is_sold"])

        return Response(BuildingAssetSerializer(asset).data, status=201)
