"""Polls and votes: a building decides things together, one vote per unit."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.apartments.models import Apartment
from apps.buildings.models import Building


class Majority(models.TextChoices):
    SIMPLE = "simple", "More than half of the votes cast"
    TWO_THIRDS = "two_thirds", "At least two thirds of the votes cast"


class Poll(models.Model):
    objects: models.Manager["Poll"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="polls")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    closes_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True, help_text="Set when an admin closes the poll early")
    # A poll can decide a pending expense: option 1 approves it, option 2 rejects it
    expense = models.ForeignKey("expenses.Expense", on_delete=models.CASCADE, null=True, blank=True, related_name="polls")
    finalized_at = models.DateTimeField(null=True, blank=True)
    # Share of eligible units that must vote for the result to count (0 = no quorum rule)
    quorum_percent = models.PositiveSmallIntegerField(default=0)
    majority = models.CharField(max_length=12, choices=Majority.choices, default=Majority.SIMPLE)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.building.name})"

    @property
    def is_open(self) -> bool:
        return self.closed_at is None and timezone.now() < self.closes_at


class PollOption(models.Model):
    objects: models.Manager["PollOption"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "text"]


class Vote(models.Model):
    """One vote per unit per poll; co-owners share it and may change it until the poll closes."""
    objects: models.Manager["Vote"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name="+")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name="votes")
    cast_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["poll", "apartment"], name="one_vote_per_unit_per_poll")]


class Meeting(models.Model):
    """Minutes of a meeting of the owners' association (محضر اجتماع), kept by the secretary."""
    objects: models.Manager["Meeting"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="meetings")
    title = models.CharField(max_length=200)
    held_on = models.DateField()
    attendees = models.TextField(blank=True)
    agenda = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    decisions = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-held_on", "-created_at"]


class DocumentKind(models.TextChoices):
    CONTRACT = "contract", "Contract"
    BYLAWS = "bylaws", "Bylaws"
    RECEIPT = "receipt", "Receipt / proof of work"
    MINUTES = "minutes", "Minutes"
    OTHER = "other", "Other"


class BuildingDocument(models.Model):
    """A file the building keeps: a contract, the bylaws, proof of work, signed minutes."""
    objects: models.Manager["BuildingDocument"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=DocumentKind.choices, default=DocumentKind.OTHER)
    file = models.FileField(upload_to="building_documents/")
    mime_type = models.CharField(max_length=60)
    size_bytes = models.PositiveIntegerField(default=0)
    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
