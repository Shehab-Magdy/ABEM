"""Payment views – Sprint 4 + Sprint 8 (PDF receipt)."""
from __future__ import annotations

import html as html_lib

from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db import transaction

from apps.apartments.models import Apartment
from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole

from .models import AssetSale, BuildingAsset, Payment
from .serializers import BuildingAssetSerializer, PaymentSerializer


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
        qs = Payment.objects.select_related("apartment", "recorded_by").prefetch_related("expenses")

        if self.request.user.role != "admin":
            # Owners see only payments for their own apartments
            qs = qs.filter(apartment__owner=self.request.user)

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
          5. Emit audit log.
        """
        apartment = serializer.validated_data["apartment"]
        amount_paid = serializer.validated_data["amount_paid"]

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

        log_action(
            user=self.request.user,
            action="create",
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
                raise PermissionDenied("You do not have permission to view this receipt.")

        def esc(value) -> str:
            """HTML-escape any user-provided value to prevent injection in the PDF."""
            return html_lib.escape(str(value))

        linked_expenses = list(payment.expenses.all())
        expense_str = (
            ", ".join(esc(e.title) for e in linked_expenses)
            if linked_expenses
            else "General payment"
        )

        recorded_by_name = (
            esc(payment.recorded_by.get_full_name() or payment.recorded_by.email)
            if payment.recorded_by else "—"
        )

        fields = [
            ("Amount Paid",    f"{payment.amount_paid:,.2f} EGP"),
            ("Payment Date",   str(payment.payment_date)),
            ("Payment Method", payment.payment_method.replace("_", " ").title()),
            ("For Expenses",   expense_str),
            ("Balance Before", f"{payment.balance_before:,.2f} EGP"),
            ("Balance After",  f"{payment.balance_after:,.2f} EGP"),
            ("Recorded By",    recorded_by_name),
            ("Notes",          esc(payment.notes or "—")),
        ]
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

        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: B5; margin: 0; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Noto Sans Arabic", "Noto Sans", Arial, sans-serif;
    font-size: 11pt;
    color: #222;
    position: relative;
    min-height: 250mm;
  }}
  .header {{
    background: #1E3A5F;
    color: white;
    padding: 10mm 20mm;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .logo {{ font-size: 22pt; font-weight: bold; }}
  .subtitle {{ font-size: 10pt; margin-top: 3px; }}
  .receipt-title {{ font-size: 14pt; font-weight: bold; text-align: right; }}
  .receipt-no {{ font-size: 9pt; text-align: right; margin-top: 4px; }}
  .info-section {{
    background: #F0F4F8;
    margin: 8mm 15mm 0;
    padding: 5mm 8mm;
    display: flex;
    justify-content: space-between;
  }}
  .info-label {{ color: #1E3A5F; font-size: 9pt; font-weight: bold; margin-bottom: 3px; }}
  .info-value {{ font-size: 11pt; unicode-bidi: plaintext; }}
  .details-table {{
    width: calc(100% - 30mm);
    margin: 6mm 15mm 0;
    border-collapse: collapse;
  }}
  .details-table tr {{ height: 12mm; }}
  .details-table tr:nth-child(odd) td {{ background: #F0F4F8; }}
  .details-table td {{ padding: 3mm 5mm; vertical-align: middle; }}
  .details-table td.lbl {{ color: #555; font-size: 9pt; font-weight: bold; width: 38%; }}
  .details-table td.val {{ text-align: right; font-size: 10pt; unicode-bidi: plaintext; }}
  .paid-box {{
    background: #E8F5E9;
    color: #2E7D32;
    font-size: 13pt;
    font-weight: bold;
    text-align: center;
    margin: 6mm 15mm 0;
    padding: 4mm;
    border-radius: 3mm;
  }}
  .footer {{
    position: absolute;
    bottom: 10mm;
    width: 100%;
    text-align: center;
    color: #888;
    font-size: 8pt;
  }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <div class="logo">ABEM</div>
      <div class="subtitle">Apartment &amp; Building Expense Management</div>
    </div>
    <div>
      <div class="receipt-title">PAYMENT RECEIPT</div>
      <div class="receipt-no">Receipt No: {str(payment.id)[:8].upper()}</div>
    </div>
  </div>

  <div class="info-section">
    <div>
      <div class="info-label">BUILDING</div>
      <div class="info-value">{esc(apt.building.name)}</div>
    </div>
    <div>
      <div class="info-label">UNIT</div>
      <div class="info-value">Unit {esc(apt.unit_number)} &nbsp;|&nbsp; {esc(apt.get_unit_type_display())}</div>
    </div>
    <div>
      <div class="info-label">OWNER</div>
      <div class="info-value">{owner_display}</div>
    </div>
  </div>

  <table class="details-table">
    {rows_html}
  </table>

  <div class="paid-box">&#10003; PAID &nbsp;&nbsp; {payment.amount_paid:,.2f} EGP &nbsp;&nbsp; RECEIVED</div>

  <div class="footer">This is an automatically generated receipt. ABEM - abem.app</div>
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
            return Response({"detail": "This asset has already been sold."}, status=400)

        sale_date = request.data.get("sale_date")
        sale_price = request.data.get("sale_price")
        if not sale_date or sale_price is None:
            return Response({"detail": "sale_date and sale_price are required."}, status=400)

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
