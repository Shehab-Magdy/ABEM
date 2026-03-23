# Generated manually — PE-01 performance enhancement

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0006_rename_notifications_broadca_idx_notificatio_broadca_93bfcc_idx'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['is_read'], name='notificatio_is_read_pe01_idx'),
        ),
    ]
