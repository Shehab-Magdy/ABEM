"""Expense views – Sprint 3."""
from __future__ import annotations

import os

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from django.utils.translation import gettext_lazy as _
from apps.apartments.models import Apartment
from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole
from apps.buildings.scoping import ensure_manages, managed_buildings

from .approval import approve as approve_expense, can_decide, reject as reject_expense
from .late_fees import waive_late_fee
from .models import Expense, ExpenseCategory, LateFee, MediaFile
from .serializers import (
    ExpenseCategorySerializer,
    ExpenseSerializer,
    MediaFileSerializer,
)


class ExpenseCategoryViewSet(ModelViewSet):
    """
    Building-scoped expense categories.

    Permissions:
      - Admin: full CRUD.
      - Owner: read-only.
    """

    serializer_class = ExpenseCategorySerializer
    http_method_names = ["get", "post", "patch", "delete", "options", "head"]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]

    # ── Scoping ────────────────────────────────────────────────────────────────

    def get_queryset(self):
        qs = ExpenseCategory.objects.filter(is_active=True).select_related("building")
        if self.request.user.role == "admin":
            qs = qs.filter(building__in=managed_buildings(self.request.user))
        else:
            qs = qs.filter(building__members=self.request.user).distinct()
        building_id = self.request.query_params.get("building_id")
        if building_id:
            qs = qs.filter(building_id=building_id)
        return qs

    # ── Permissions ────────────────────────────────────────────────────────────

    def get_permissions(self):
        if self.action in ("create", "partial_update", "update", "destroy"):
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    # ── Write helpers ──────────────────────────────────────────────────────────

    def perform_create(self, serializer):
        ensure_manages(self.request.user, serializer.validated_data["building"])
        category = serializer.save()
        log_action(
            user=self.request.user,
            action="create",
            entity="expense_category",
            entity_id=category.pk,
            request=self.request,
        )

    def perform_destroy(self, instance):
        log_action(
            user=self.request.user,
            action="delete",
            entity="expense_category",
            entity_id=instance.pk,
            request=self.request,
        )
        # Soft-deactivate (expenses reference categories via PROTECT)
        instance.is_active = False
        instance.save()


class ExpenseViewSet(ModelViewSet):
    """
    Expense CRUD with split engine + optional bill file upload.

    Permissions:
      - Admin: full CRUD + upload action.
      - Owner: read-only (expenses for buildings they are members of).
      - Unauthenticated: 401.
    """

    serializer_class = ExpenseSerializer
    http_method_names = ["get", "post", "patch", "delete", "options", "head"]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["split_type", "is_recurring", "kind"]
    search_fields = ["title", "description"]
    ordering_fields = ["expense_date", "amount", "created_at"]
    ordering = ["-expense_date"]

    # ── Scoping ────────────────────────────────────────────────────────────────

    def get_queryset(self):
        qs = Expense.objects.filter(deleted_at__isnull=True).select_related(
            "building", "category", "created_by"
        ).prefetch_related(
            "apartment_expenses", "apartment_expenses__apartment"
        )

        building_id = self.request.query_params.get("building_id")
        if building_id:
            qs = qs.filter(building_id=building_id)

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(expense_date__gte=date_from)
        if date_to:
            qs = qs.filter(expense_date__lte=date_to)

        category_id = self.request.query_params.get("category_id")
        if category_id:
            qs = qs.filter(category_id=category_id)

        if self.request.user.role == "admin":
            return qs.filter(building__in=managed_buildings(self.request.user))
        return qs.filter(building__members=self.request.user)

    # ── Permissions ────────────────────────────────────────────────────────────

    def get_permissions(self):
        write_actions = ("create", "partial_update", "update", "destroy", "upload", "mark_paid")  # approve / reject / put_to_vote check the chair themselves
        if self.action in write_actions:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    # ── Write helpers ──────────────────────────────────────────────────────────

    def perform_create(self, serializer):
        ensure_manages(self.request.user, serializer.validated_data["building"])
        expense = serializer.save(created_by=self.request.user)
        log_action(
            user=self.request.user,
            action="create",
            entity="expense",
            entity_id=expense.pk,
            request=self.request,
        )
        try:
            from apps.notifications.services import notify_expense_created
            from .models import ApartmentExpense
            ae_list = list(
                ApartmentExpense.objects.filter(expense=expense)
                .select_related("apartment__owner")
            )
            notify_expense_created(expense, [ae.apartment for ae in ae_list])
        except Exception:
            pass

    def _decider(self, request):
        """The pending expense, if the user may decide on it (the chair, or an admin while no chair is named)."""
        expense = self.get_object()
        if not can_decide(request.user, expense.building):
            raise PermissionDenied(_("Only the building's chair can decide on this expense."))
        if expense.approval_status != "pending":
            return expense, Response({"detail": _("This expense is not waiting for approval.")}, status=409)
        return expense, None

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        expense, conflict = self._decider(request)
        if conflict:
            return conflict
        expense = approve_expense(expense, request.user, str(request.data.get("note") or ""))
        log_action(user=request.user, action="update", entity="expense", entity_id=expense.pk, changes={"approval": "approved"}, request=request)
        return Response(self.get_serializer(expense).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        expense, conflict = self._decider(request)
        if conflict:
            return conflict
        expense = reject_expense(expense, request.user, str(request.data.get("note") or ""))
        log_action(user=request.user, action="update", entity="expense", entity_id=expense.pk, changes={"approval": "rejected"}, request=request)
        return Response(self.get_serializer(expense).data)

    @action(detail=True, methods=["post"], url_path="put-to-vote")
    def put_to_vote(self, request, pk=None):
        """Let the residents decide: opens a poll (approve / reject, one vote per unit); its outcome settles the expense."""
        from datetime import timedelta

        from apps.governance.models import Poll, PollOption
        from apps.notifications.models import NotificationType
        from apps.notifications.services import notify_user

        expense, conflict = self._decider(request)
        if conflict:
            return conflict
        if expense.polls.filter(finalized_at__isnull=True).exists():
            return Response({"detail": _("A vote on this expense is already open.")}, status=409)
        ar = getattr(request.user, "preferred_language", "ar") == "ar"
        poll = Poll.objects.create(
            building=expense.building, expense=expense, created_by=request.user,
            title=(f"الموافقة على مصروف: {expense.title} ({expense.amount})" if ar else f"Approve this expense: {expense.title} ({expense.amount})"),
            description=expense.description, closes_at=timezone.now() + timedelta(days=int(request.data.get("days") or 3)),
            quorum_percent=int(request.data.get("quorum_percent") or 0),
        )
        PollOption.objects.bulk_create([
            PollOption(poll=poll, text="موافق" if ar else "Approve", order=0),
            PollOption(poll=poll, text="غير موافق" if ar else "Reject", order=1),
        ])
        for member in expense.building.members.exclude(pk=request.user.pk):
            notify_user(user=member, notification_type=NotificationType.ANNOUNCEMENT,
                        title="تصويت جديد" if getattr(member, "preferred_language", "en") == "ar" else "New vote",
                        body=poll.title, category="announcements", metadata={"poll_id": str(poll.pk)})
        return Response({"poll_id": str(poll.pk)}, status=201)

    def perform_update(self, serializer):
        tracked = {
            field: str(getattr(serializer.instance, field, ""))
            for field in serializer.validated_data
            if field not in ("frequency", "custom_split_apartments")
            and hasattr(serializer.instance, field)
        }
        instance = serializer.save()
        changes = {
            field: {"before": tracked[field], "after": str(getattr(instance, field, ""))}
            for field in tracked
        }
        log_action(
            user=self.request.user,
            action="update",
            entity="expense",
            entity_id=instance.pk,
            changes=changes,
            request=self.request,
        )

    def perform_destroy(self, instance):
        from django.core.files.storage import default_storage

        # Delete physical files and MediaFile records before soft-deleting
        media_files = MediaFile.objects.filter(entity_type="expense", entity_id=instance.pk)
        for mf in media_files:
            try:
                # url is typically "/media/expenses/<file>" — derive storage path
                storage_name = mf.url.lstrip("/")
                if storage_name.startswith("media/"):
                    storage_name = storage_name[len("media/"):]
                if default_storage.exists(storage_name):
                    default_storage.delete(storage_name)
            except Exception:
                pass
        media_files.delete()

        log_action(
            user=self.request.user,
            action="delete",
            entity="expense",
            entity_id=instance.pk,
            request=self.request,
        )
        with transaction.atomic():
            # Take the expense's shares back off each apartment's balance
            for share in instance.apartment_expenses.all():
                Apartment.objects.filter(pk=share.apartment_id).update(
                    balance=F("balance") - share.share_amount
                )
            instance.apartment_expenses.all().delete()
            instance.deleted_at = timezone.now()
            instance.save()

    # ── Mark as paid ──────────────────────────────────────────────────────────

    @action(
        detail=True,
        methods=["post"],
        url_path="mark_paid",
        permission_classes=[IsAuthenticated, IsAdminRole],
    )
    def mark_paid(self, request, pk=None):
        """
        POST /expenses/{id}/mark_paid/
        Toggle the is_manually_paid flag (admin only).
        """
        expense = self.get_object()
        expense.is_manually_paid = not expense.is_manually_paid
        expense.save(update_fields=["is_manually_paid"])
        log_action(
            user=request.user,
            action="expense.marked_paid",
            entity="expense",
            entity_id=expense.id,
            changes={"is_manually_paid": {"after": expense.is_manually_paid}},
            request=request,
        )
        return Response(self.get_serializer(expense).data)

    # ── File upload ────────────────────────────────────────────────────────────

    @action(
        detail=True,
        methods=["post"],
        url_path="upload",
        permission_classes=[IsAuthenticated, IsAdminRole],
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload(self, request, pk=None):
        """
        POST /expenses/{id}/upload/
        Attach a bill image (JPEG/PNG) or PDF to this expense.
        Enforces MIME type and MAX_UPLOAD_SIZE_MB limits.
        """
        expense = self.get_object()

        if "file" not in request.FILES:
            return Response(
                {"detail": _("No file provided. Use multipart/form-data with key 'file'.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded = request.FILES["file"]
        mime_type = uploaded.content_type

        allowed_types = getattr(
            settings, "ALLOWED_UPLOAD_TYPES", ["image/jpeg", "image/png", "application/pdf"]
        )
        max_bytes = getattr(settings, "MAX_UPLOAD_SIZE_MB", 10) * 1024 * 1024

        if mime_type not in allowed_types:
            return Response(
                {
                    "detail": _("Unsupported file type '%(mime_type)s'. "
                                "Allowed types: %(allowed_types)s") % {
                        "mime_type": mime_type,
                        "allowed_types": allowed_types,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if uploaded.size > max_bytes:
            return Response(
                {
                    "detail": _("File size %(size)s bytes exceeds the "
                                "%(limit)s MB limit.") % {
                        "size": uploaded.size,
                        "limit": settings.MAX_UPLOAD_SIZE_MB,
                    }
                },
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage

        ext = os.path.splitext(uploaded.name)[1] or ""
        filename = f"expenses/{expense.pk}{ext}"
        saved_name = default_storage.save(filename, ContentFile(uploaded.read()))
        file_url = default_storage.url(saved_name)

        media_file = MediaFile.objects.create(
            entity_type="expense",
            entity_id=expense.pk,
            url=file_url,
            mime_type=mime_type,
            file_size_bytes=uploaded.size,
            uploaded_by=request.user,
        )

        log_action(
            user=request.user,
            action="upload",
            entity="expense",
            entity_id=expense.pk,
            changes={"file": {"before": None, "after": file_url}},
            request=request,
        )

        return Response(MediaFileSerializer(media_file).data, status=status.HTTP_200_OK)


class LateFeeViewSet(ReadOnlyModelViewSet):
    """
    GET  /expenses/late-fees/?building_id=        – late fees in buildings the admin manages
    POST /expenses/late-fees/{id}/waive/ {reason} – take a fee back off the unit (recorded with who and why)
    """

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        qs = LateFee.objects.select_related("expense__building", "share__apartment", "waived_by").filter(
            expense__building__in=managed_buildings(self.request.user)
        )
        if building_id := self.request.query_params.get("building_id"):
            qs = qs.filter(expense__building_id=building_id)
        if self.request.query_params.get("waived") == "false":
            qs = qs.filter(waived_at__isnull=True)
        return qs.order_by("-created_at")

    def get_serializer_class(self):
        from rest_framework import serializers

        class LateFeeSerializer(serializers.ModelSerializer):
            building_name = serializers.CharField(source="expense.building.name", read_only=True)
            unit_number = serializers.CharField(source="share.apartment.unit_number", read_only=True)
            amount = serializers.DecimalField(source="expense.amount", max_digits=10, decimal_places=2, read_only=True)
            title = serializers.CharField(source="expense.title", read_only=True)

            class Meta:
                model = LateFee
                fields = ["id", "building_name", "unit_number", "title", "amount", "created_at", "waived_at", "waived_reason"]

        return LateFeeSerializer

    @action(detail=True, methods=["post"], url_path="waive")
    def waive(self, request, pk=None):
        fee = waive_late_fee(self.get_object(), request.user, str(request.data.get("reason") or ""))
        log_action(
            user=request.user, action="update", entity="late_fee", entity_id=fee.pk,
            changes={"waived": True, "reason": fee.waived_reason}, request=request,
        )
        return Response(self.get_serializer(fee).data)
