"""Which audit rows belong to which buildings: by the entity they touched, never by who acted."""
from apps.apartments.models import Apartment
from apps.expenses.models import Expense
from apps.payments.models import Payment, PaymentClaim
from apps.plans.models import PlanPayment
from django.db.models import Q

from .models import AuditLog


def audit_for_buildings(buildings, own_user=None):
    """Audit rows about the given buildings (a queryset of Building), plus own_user's own actions."""
    q = (
        Q(entity_id__in=buildings.values("id"))
        | Q(entity_id__in=Apartment.objects.filter(building__in=buildings).values("id"))
        | Q(entity_id__in=Expense.objects.filter(building__in=buildings).values("id"))
        | Q(entity_id__in=Payment.objects.filter(apartment__building__in=buildings).values("id"))
        | Q(entity_id__in=PaymentClaim.objects.filter(apartment__building__in=buildings).values("id"))
        | Q(entity_id__in=PlanPayment.objects.filter(building__in=buildings).values("id"))
        | Q(changes__building_id__in=[str(pk) for pk in buildings.values_list("pk", flat=True)])
    )
    if own_user is not None:
        q |= Q(user=own_user)
    return AuditLog.objects.filter(q)
