from rest_framework import serializers

from .models import SupportTicket

MAX_SCREENSHOT_BYTES = 5 * 1024 * 1024


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ["id", "message", "screenshot", "page", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate_message(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("Please describe the problem in a few words.")
        return value

    def validate_screenshot(self, value):
        if value and value.size > MAX_SCREENSHOT_BYTES:
            raise serializers.ValidationError("The screenshot must be smaller than 5 MB.")
        return value
