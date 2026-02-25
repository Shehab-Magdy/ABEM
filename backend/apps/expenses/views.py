"""Expense views – Sprint 3."""
from __future__ import annotations

import os

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole

from .models import Expense, ExpenseCategory, MediaFile
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
    filterset_fields = ["split_type", "is_recurring"]
    search_fields = ["title", "description"]
    ordering_fields = ["expense_date", "amount", "created_at"]
    ordering = ["-expense_date"]

    # ── Scoping ────────────────────────────────────────────────────────────────

    def get_queryset(self):
        qs = Expense.objects.filter(deleted_at__isnull=True).select_related(
            "building", "category", "created_by"
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
            return qs
        return qs.filter(building__members=self.request.user)

    # ── Permissions ────────────────────────────────────────────────────────────

    def get_permissions(self):
        write_actions = ("create", "partial_update", "update", "destroy", "upload")
        if self.action in write_actions:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    # ── Write helpers ──────────────────────────────────────────────────────────

    def perform_create(self, serializer):
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
        log_action(
            user=self.request.user,
            action="delete",
            entity="expense",
            entity_id=instance.pk,
            request=self.request,
        )
        instance.deleted_at = timezone.now()
        instance.save()

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
                {"detail": "No file provided. Use multipart/form-data with key 'file'."},
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
                    "detail": (
                        f"Unsupported file type '{mime_type}'. "
                        f"Allowed types: {allowed_types}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if uploaded.size > max_bytes:
            return Response(
                {
                    "detail": (
                        f"File size {uploaded.size} bytes exceeds the "
                        f"{settings.MAX_UPLOAD_SIZE_MB} MB limit."
                    )
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
