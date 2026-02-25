"""Notification serializers – Sprint 6."""
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "channel",
            "title",
            "body",
            "is_read",
            "metadata",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "notification_type",
            "channel",
            "title",
            "body",
            "metadata",
            "created_at",
        ]


class BroadcastSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField()
    building_id = serializers.UUIDField()
