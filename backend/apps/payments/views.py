"""Payment views – stubs to be fully implemented in Sprint 4."""
from rest_framework.viewsets import ModelViewSet
from .models import Payment


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.none()
    # TODO Sprint 4: balance engine, partial/over payment, carry-forward
