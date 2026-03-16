from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_add_profile_picture_to_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='messaging_blocked',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='individual_messaging_blocked',
            field=models.BooleanField(default=False),
        ),
    ]
