from django.db import migrations

PLANS = [
    ("free", "مجانية", "Free", "0", "0", 10, [], 0),
    ("standard", "أساسية", "Standard", "99", "990", 40, ["subscriptions"], 1),
    ("plus", "متقدمة", "Plus", "249", "2490", None, ["subscriptions", "annual_report"], 2),
]


def seed(apps, schema_editor):
    Plan = apps.get_model("plans", "Plan")
    for code, ar, en, monthly, yearly, units, features, order in PLANS:
        Plan.objects.get_or_create(code=code, defaults={
            "name_ar": ar, "name_en": en, "price_monthly": monthly, "price_yearly": yearly,
            "max_units": units, "features": features, "sort_order": order,
        })
    apps.get_model("plans", "PlatformSettings").objects.get_or_create()


class Migration(migrations.Migration):
    dependencies = [("plans", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
