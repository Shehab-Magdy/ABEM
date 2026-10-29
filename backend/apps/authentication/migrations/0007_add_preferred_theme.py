from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0006_add_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="preferred_theme",
            field=models.CharField(
                choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")],
                default="system",
                max_length=6,
            ),
        ),
    ]
