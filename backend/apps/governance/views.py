from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.decorators import action
from django.conf import settings
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.apartments.models import Apartment
from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole
from apps.buildings.scoping import ensure_manages, has_board_role, managed_buildings
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_user

from .finalize import apply_poll_outcome
from .models import BuildingDocument, Meeting, Poll, PollOption, Vote
from .results import can_vote_for
from .serializers import DocumentSerializer, MeetingSerializer, PollSerializer


class PollViewSet(ModelViewSet):
    """
    GET  /governance/polls/                – admins: polls in buildings they manage; residents: their building's polls
    POST /governance/polls/                – admin creates a poll (2-10 options, closing time, optional quorum/majority)
    POST /governance/polls/{id}/vote/      – an owner votes for a unit ({option_id, apartment_id}); one vote per unit
    POST /governance/polls/{id}/close/     – admin closes it early
    """

    serializer_class = PollSerializer
    http_method_names = ["get", "post", "options", "head"]

    def get_queryset(self):
        qs = Poll.objects.select_related("building").prefetch_related("options")
        user = self.request.user
        if user.role == "admin":
            qs = qs.filter(building__in=managed_buildings(user))
        else:
            qs = qs.filter(building__members=user).distinct()
        if building_id := self.request.query_params.get("building_id"):
            qs = qs.filter(building_id=building_id)
        return qs

    def get_permissions(self):
        if self.action in ("create", "close"):
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        ensure_manages(self.request.user, serializer.validated_data["building"])
        poll = serializer.save(created_by=self.request.user)
        log_action(user=self.request.user, action="create", entity="poll", entity_id=poll.pk, request=self.request)
        for member in poll.building.members.exclude(pk=self.request.user.pk):
            notify_user(
                user=member,
                notification_type=NotificationType.ANNOUNCEMENT,
                title="تصويت جديد" if getattr(member, "preferred_language", "en") == "ar" else "New vote",
                body=poll.title,
                metadata={"poll_id": str(poll.pk)},
            )

    @action(detail=True, methods=["post"], url_path="vote")
    def vote(self, request, pk=None):
        poll = self.get_object()
        if not poll.is_open:
            return Response({"detail": _("This vote is closed.")}, status=409)
        try:
            apartment = Apartment.objects.get(pk=request.data.get("apartment_id"), building=poll.building)
            option = PollOption.objects.get(pk=request.data.get("option_id"), poll=poll)
        except (Apartment.DoesNotExist, PollOption.DoesNotExist, ValueError, TypeError):
            return Response({"detail": _("Choose one of this vote's options for your unit.")}, status=400)
        if not can_vote_for(request.user, apartment):
            raise PermissionDenied(_("Only an owner of this unit can vote for it."))
        Vote.objects.update_or_create(
            poll=poll, apartment=apartment, defaults={"option": option, "cast_by": request.user}
        )
        return Response(self.get_serializer(poll).data)

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        poll = self.get_object()
        if not poll.is_open:
            return Response({"detail": _("This vote is already closed.")}, status=409)
        poll.closed_at = timezone.now()
        poll.save(update_fields=["closed_at"])
        apply_poll_outcome(poll)  # a poll about an expense settles it now
        log_action(user=request.user, action="update", entity="poll", entity_id=poll.pk, request=request)
        return Response(self.get_serializer(poll).data)


def _can_write_records(user, building) -> bool:
    """Minutes and documents are kept by the building's admins and its secretary."""
    return managed_buildings(user).filter(pk=getattr(building, "pk", building)).exists() or has_board_role(user, building, "secretary")


def _visible_buildings(user):
    """Buildings whose records this user may read: managed (admins) or member (everyone else)."""
    from apps.buildings.models import Building

    if user.role == "admin":
        return managed_buildings(user)
    return Building.objects.filter(members=user, deleted_at__isnull=True)


class MeetingViewSet(ModelViewSet):
    """
    GET    /governance/meetings/              – minutes of the user's buildings (all members read)
    POST   /governance/meetings/              – the secretary or an admin records a meeting
    PATCH  /governance/meetings/{id}/         – edit
    GET    /governance/meetings/{id}/pdf/     – one-page PDF (in the user's language)
    """

    serializer_class = MeetingSerializer
    http_method_names = ["get", "post", "patch", "delete", "options", "head"]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Meeting.objects.select_related("building").filter(building__in=_visible_buildings(self.request.user))
        if building_id := self.request.query_params.get("building_id"):
            qs = qs.filter(building_id=building_id)
        return qs

    def _check_write(self, building):
        if not _can_write_records(self.request.user, building):
            raise PermissionDenied(_("Only the building's secretary or admins can keep the minutes."))

    def perform_create(self, serializer):
        self._check_write(serializer.validated_data["building"])
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        self._check_write(serializer.instance.building)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_write(instance.building)
        instance.delete()

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        from django.http import HttpResponse

        from .minutes import render_minutes_pdf

        meeting = self.get_object()
        try:
            data = render_minutes_pdf(meeting, getattr(request.user, "preferred_language", None) or "ar")
        except Exception as exc:  # WeasyPrint or its system libraries missing
            return Response({"detail": f"PDF generation failed: {exc}"}, status=503)
        response = HttpResponse(data, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="minutes_{meeting.held_on}.pdf"'
        return response


class DocumentViewSet(ModelViewSet):
    """
    GET    /governance/documents/         – the building's files (all members read)
    POST   /governance/documents/         – multipart: building_id, title, kind, file (PDF/JPEG/PNG) — secretary or admin
    DELETE /governance/documents/{id}/    – secretary or admin
    """

    serializer_class = DocumentSerializer
    http_method_names = ["get", "post", "delete", "options", "head"]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = BuildingDocument.objects.select_related("building", "uploaded_by").filter(building__in=_visible_buildings(self.request.user))
        if building_id := self.request.query_params.get("building_id"):
            qs = qs.filter(building_id=building_id)
        return qs

    def perform_create(self, serializer):
        building = serializer.validated_data["building"]
        if not _can_write_records(self.request.user, building):
            raise PermissionDenied(_("Only the building's secretary or admins can keep the minutes."))
        upload = self.request.FILES.get("file")
        if upload is None:
            raise ValidationError({"file": _("Attach a file.")})
        allowed = getattr(settings, "ALLOWED_UPLOAD_TYPES", ["image/jpeg", "image/png", "application/pdf"])
        if upload.content_type not in allowed:
            raise ValidationError({"file": _("Only PDF, JPEG or PNG files are allowed.")})
        if upload.size > getattr(settings, "MAX_UPLOAD_SIZE_MB", 10) * 1024 * 1024:
            raise ValidationError({"file": _("The file is too large.")})
        serializer.save(file=upload, mime_type=upload.content_type, size_bytes=upload.size, uploaded_by=self.request.user)

    def perform_destroy(self, instance):
        if not _can_write_records(self.request.user, instance.building):
            raise PermissionDenied(_("Only the building's secretary or admins can keep the minutes."))
        instance.file.delete(save=False)
        instance.delete()
