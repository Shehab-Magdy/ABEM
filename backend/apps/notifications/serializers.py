"""Notification serializers – Sprint 6."""
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    def get_sender_name(self, obj):
        if obj.sender:
            return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email
        return None

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
            "sender_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "notification_type",
            "channel",
            "title",
            "body",
            "metadata",
            "sender_name",
            "created_at",
        ]


class BroadcastSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField()
    building_id = serializers.UUIDField()
