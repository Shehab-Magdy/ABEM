from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.apartments.models import Apartment
from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole
from apps.buildings.scoping import ensure_manages, managed_buildings
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_user

from .finalize import apply_poll_outcome
from .models import Poll, PollOption, Vote
from .results import can_vote_for
from .serializers import PollSerializer


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
