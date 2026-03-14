"""
Management command to seed default expense categories for all buildings
that don't have any categories yet.

Usage:
    python manage.py seed_expense_categories
"""
from django.core.management.base import BaseCommand

from apps.buildings.models import Building
from apps.expenses.models import ExpenseCategory

DEFAULT_CATEGORIES = [
    ("Maintenance", "Repairs and upkeep"),
    ("Utilities", "Electricity, water, and gas"),
    ("Cleaning", "Cleaning and janitorial services"),
    ("Security", "Security personnel and systems"),
    ("Management", "Administrative and management fees"),
    ("Other", "Miscellaneous expenses"),
]


class Command(BaseCommand):
    help = "Seed default expense categories for buildings that have none."

    def handle(self, *args, **options):
        buildings = Building.objects.filter(
            is_active=True, deleted_at__isnull=True
        ).exclude(expense_categories__isnull=False)

        if not buildings.exists():
            self.stdout.write("All buildings already have categories. Nothing to do.")
            return

        total = 0
        for building in buildings:
            categories = [
                ExpenseCategory(building=building, name=name, description=desc)
                for name, desc in DEFAULT_CATEGORIES
            ]
            ExpenseCategory.objects.bulk_create(categories, ignore_conflicts=True)
            total += len(categories)
            self.stdout.write(f"  Seeded {len(categories)} categories for '{building.name}'")

        self.stdout.write(self.style.SUCCESS(f"Done. Created {total} categories across {buildings.count()} buildings."))
