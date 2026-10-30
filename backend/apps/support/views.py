from django.conf import settings
from django.core.mail import send_mail
from rest_framework import mixins, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from .models import SupportTicket
from .serializers import SupportTicketSerializer


class SupportTicketViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Users send problem reports and see their own; the team reads all of them in the Django admin."""

    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        ticket = serializer.save(user=self.request.user)
        if settings.SUPPORT_EMAIL:
            send_mail(
                subject=f"[3maracom] Problem report from {self.request.user.email}",
                message=f"{ticket.message}\n\nScreenshot: {'yes (see admin)' if ticket.screenshot else 'no'}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SUPPORT_EMAIL],
                fail_silently=True,
            )
