from django.core.management.base import BaseCommand

from apps.expenses.recurring import generate_recurring_expenses


class Command(BaseCommand):
    help = "Create the next copy of every recurring expense that is due. Run once a day (cron / scheduler)."

    def handle(self, *args, **options):
        created = generate_recurring_expenses()
        self.stdout.write(self.style.SUCCESS(f"Created {created} recurring expense(s)."))
