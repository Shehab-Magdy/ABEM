"""Quick maintenance reports from residents (بلاغ صيانة)."""
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.apartments.models import Apartment
from apps.buildings.models import Building


class ReportCategory(models.TextChoices):
    ELEVATOR = "elevator", _("Elevator")
    STAIRS = "stairs", _("Stairs")
    CLEANING = "cleaning", _("Cleaning")
    ELECTRICITY = "electricity", _("Electricity")
    WATER = "water", _("Water")
    OTHER = "other", _("Other")


class ReportStatus(models.TextChoices):
    OPEN = "open", _("Open")
    IN_PROGRESS = "in_progress", _("In progress")
    DONE = "done", _("Done")


class MaintenanceReport(models.Model):
    objects: models.Manager["MaintenanceReport"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="maintenance_reports")
    apartment = models.ForeignKey(Apartment, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="maintenance_reports"
    )
    category = models.CharField(max_length=20, choices=ReportCategory.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=ReportStatus.choices, default=ReportStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["building", "status"])]

    def __str__(self):
        return f"{self.get_category_display()} – {self.building.name} ({self.status})"


class WorkOrderStatus(models.TextChoices):
    ASSIGNED = "assigned", _("Assigned")
    IN_PROGRESS = "in_progress", _("In progress")
    DONE = "done", _("Done")


class WorkOrder(models.Model):
    """A maintenance report taken on: who does the work, when, and which expense it cost."""
    objects: models.Manager["WorkOrder"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.OneToOneField(MaintenanceReport, on_delete=models.CASCADE, related_name="work_order")
    contractor = models.ForeignKey("operations.Contractor", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders")
    scheduled_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=WorkOrderStatus.choices, default=WorkOrderStatus.ASSIGNED)
    completed_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    # The cost, once it is recorded as an expense of the same building
    expense = models.ForeignKey("expenses.Expense", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
