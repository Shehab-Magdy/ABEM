"""Payment views – Sprint 4."""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from django.db import transaction

from apps.apartments.models import Apartment
from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole

from .models import Payment
from .serializers import PaymentSerializer


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
