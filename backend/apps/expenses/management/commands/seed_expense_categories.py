"""
Management command to seed default expense categories for all buildings
that don't have any categories yet.

Usage:
    python manage.py seed_expense_categories
    python manage.py seed_expense_categories --all   # re-seed even existing buildings
"""
from django.core.management.base import BaseCommand

from apps.buildings.models import Building
from apps.expenses.models import ExpenseCategory

# (name, description, Material icon name, hex color)
DEFAULT_CATEGORIES = [
    ("Maintenance", "General repairs and structural upkeep", "build", "#2563EB"),
    ("Utilities", "Electricity, water, gas, and fuel", "bolt", "#F59E0B"),
    ("Cleaning", "Cleaning and janitorial services", "cleaning_services", "#10B981"),
    ("Security", "Guards, cameras, and access control systems", "security", "#7C3AED"),
    ("Elevator", "Elevator servicing, repairs, and inspection", "elevator", "#EA580C"),
    ("Plumbing",         "Plumbing repairs and water system maintenance","plumbing",             "#0EA5E9"),
    ("Internet & Cable", "Shared internet, satellite, and cable TV", "wifi", "#6366F1"),
    ("Parking", "Parking area maintenance and management", "local_parking", "#64748B"),
    ("Landscaping", "Gardens, green areas, and outdoor spaces", "yard", "#16A34A"),
    ("Pest Control", "Pest and rodent extermination services", "pest_control", "#DC2626"),
    ("Fire Safety", "Fire extinguishers, alarms, and inspections", "fire_extinguisher", "#EF4444"),
    ("Waste Management", "Waste collection and recycling services", "delete_sweep", "#78716C"),
    ("Insurance", "Building and common area insurance premiums", "shield", "#0369A1"),
    ("Management", "Administrative and property management fees", "admin_panel_settings", "#1F2937"),
    ("Other", "Miscellaneous and one-off expenses", "category", "#6B7280"),
]


class Command(BaseCommand):
    help = "Seed default expense categories for buildings that have none."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Re-seed all active buildings, not just those without categories.",
        )

    def handle(self, *args, **options):
        qs = Building.objects.filter(is_active=True, deleted_at__isnull=True)
        if not options["all"]:
            qs = qs.exclude(expense_categories__isnull=False)

        if not qs.exists():
            self.stdout.write("All buildings already have categories. Use --all to re-seed.")
            return

        total = 0
        for building in qs:
            for name, desc, icon, color in DEFAULT_CATEGORIES:
                _, created = ExpenseCategory.objects.get_or_create(
                    building=building,
                    name=name,
                    defaults={"description": desc, "icon": icon, "color": color},
                )
                if created:
                    total += 1
            self.stdout.write(f"  Seeded categories for '{building.name}'")

        self.stdout.write(self.style.SUCCESS(f"Done. Created {total} new categories."))
