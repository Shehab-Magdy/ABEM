"""Contractors and the calendar of recurring obligations (elevator contract, fire extinguishers, tank cleaning ...)."""
import uuid

from django.db import models

from apps.buildings.models import Building


class Contractor(models.Model):
    objects: models.Manager["Contractor"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="contractors")
    name = models.CharField(max_length=150)
    trade = models.CharField(max_length=80, blank=True)          # elevator technician, plumber, cleaner ...
    phone = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)       # renewal reminders start 30 days before
    is_active = models.BooleanField(default=True)
    last_reminded_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.building.name})"


class Repeat(models.TextChoices):
    NONE = "none", "Once"
    MONTHLY = "monthly", "Monthly"
    QUARTERLY = "quarterly", "Every 3 months"
    YEARLY = "yearly", "Yearly"


class Obligation(models.Model):
    objects: models.Manager["Obligation"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="obligations")
    title = models.CharField(max_length=200)
    due_date = models.DateField()
    repeat = models.CharField(max_length=10, choices=Repeat.choices, default=Repeat.NONE)
    contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True, related_name="obligations")
    notes = models.TextField(blank=True)
    remind_days = models.PositiveSmallIntegerField(default=14)   # start reminding this many days before it is due
    is_active = models.BooleanField(default=True)                # a one-off becomes inactive once done
    last_done_on = models.DateField(null=True, blank=True)
    last_reminded_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date"]
