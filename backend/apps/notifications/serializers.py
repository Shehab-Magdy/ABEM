"""Notification serializers – Sprint 6."""
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    total_recipients = serializers.SerializerMethodField()

    def get_sender_name(self, obj):
        if obj.sender:
            return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email
        return None

    def _is_admin_request(self):
        request = self.context.get("request")
        return request and hasattr(request, "user") and request.user.role == "admin"

    def get_read_count(self, obj):
        if not self._is_admin_request():
            return None
        if not obj.broadcast_group:
            return None
        return Notification.objects.filter(
            broadcast_group=obj.broadcast_group, is_read=True
        ).count()

    def get_total_recipients(self, obj):
        if not self._is_admin_request():
            return None
        if not obj.broadcast_group:
            return None
        return Notification.objects.filter(
            broadcast_group=obj.broadcast_group
        ).count()

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
            "read_count",
            "total_recipients",
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
            "read_count",
            "total_recipients",
            "created_at",
        ]


class BroadcastSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField()
    building_id = serializers.UUIDField()
