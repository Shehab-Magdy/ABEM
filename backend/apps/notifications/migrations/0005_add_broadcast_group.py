# Generated migration for broadcast_group field.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0004_add_message_notification_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="broadcast_group",
            field=models.UUIDField(
                blank=True,
                help_text="Groups notifications from the same broadcast/announcement.",
                null=True,
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["broadcast_group"],
                name="notifications_broadca_idx",
            ),
        ),
    ]
