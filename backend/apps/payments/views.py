"""Payment views – Sprint 4 + Sprint 8 (PDF receipt)."""
from __future__ import annotations

import io

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
        qs = Payment.objects.select_related("apartment", "expense", "recorded_by")

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
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as rl_canvas

        payment = self.get_object()

        # Owners may only view receipts for their own apartments
        apt = payment.apartment
        if request.user.role != "admin":
            is_owner = (apt.owner == request.user) or apt.owners.filter(pk=request.user.pk).exists()
            if not is_owner:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You do not have permission to view this receipt.")

        buf = io.BytesIO()
        width, height = A4
        c = rl_canvas.Canvas(buf, pagesize=A4)

        # ── Header bar ─────────────────────────────────────────────────────────
        c.setFillColor(colors.HexColor("#1E3A5F"))
        c.rect(0, height - 60 * mm, width, 60 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(20 * mm, height - 28 * mm, "ABEM")
        c.setFont("Helvetica", 11)
        c.drawString(20 * mm, height - 40 * mm, "Apartment & Building Expense Management")
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(width - 20 * mm, height - 28 * mm, "PAYMENT RECEIPT")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 20 * mm, height - 40 * mm, f"Receipt No: {str(payment.id)[:8].upper()}")

        # ── Building & Unit info ────────────────────────────────────────────────
        y = height - 80 * mm
        c.setFillColor(colors.HexColor("#F0F4F8"))
        c.rect(15 * mm, y - 30 * mm, width - 30 * mm, 30 * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#1E3A5F"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20 * mm, y - 10 * mm, "BUILDING")
        c.drawString(width / 2, y - 10 * mm, "UNIT")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 11)
        c.drawString(20 * mm, y - 20 * mm, apt.building.name)
        c.drawString(width / 2, y - 20 * mm, f"Unit {apt.unit_number}  ·  {apt.get_unit_type_display()}")

        # ── Payment details ─────────────────────────────────────────────────────
        y -= 45 * mm
        fields = [
            ("Amount Paid",    f"{payment.amount_paid:,.2f} EGP"),
            ("Payment Date",   str(payment.payment_date)),
            ("Payment Method", payment.payment_method.replace("_", " ").title()),
            ("Balance Before", f"{payment.balance_before:,.2f} EGP"),
            ("Balance After",  f"{payment.balance_after:,.2f} EGP"),
            ("Recorded By",    str(payment.recorded_by or "—")),
            ("Notes",          payment.notes or "—"),
        ]
        row_h = 12 * mm
        for label, value in fields:
            c.setFillColor(colors.HexColor("#F0F4F8"))
            c.rect(15 * mm, y - row_h + 3 * mm, width - 30 * mm, row_h, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#555555"))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(20 * mm, y, label)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 10)
            c.drawRightString(width - 20 * mm, y, value)
            y -= row_h + 1 * mm

        # ── Highlight amount ───────────────────────────────────────────────────
        c.setFillColor(colors.HexColor("#E8F5E9"))
        c.roundRect(15 * mm, y - 16 * mm, width - 30 * mm, 14 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#2E7D32"))
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(width / 2, y - 8 * mm, f"✓  {payment.amount_paid:,.2f} EGP  RECEIVED")

        # ── Footer ─────────────────────────────────────────────────────────────
        c.setFillColor(colors.HexColor("#888888"))
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, 15 * mm, "This is an automatically generated receipt. ABEM — abem.app")

        c.save()
        buf.seek(0)

        resp = HttpResponse(buf.read(), content_type="application/pdf")
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
