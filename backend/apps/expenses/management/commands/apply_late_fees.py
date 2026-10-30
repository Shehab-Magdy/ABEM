from django.core.management.base import BaseCommand

from apps.expenses.late_fees import apply_late_fees


class Command(BaseCommand):
    help = "Add late fees to overdue subscription shares (for buildings that use them). Run daily."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Created {apply_late_fees()} late fee(s)."))
