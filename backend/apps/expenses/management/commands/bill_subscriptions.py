from django.core.management.base import BaseCommand

from apps.expenses.subscriptions import bill_subscriptions


class Command(BaseCommand):
    help = "Charge every unit its monthly subscription once the building's billing day has arrived. Run daily."

    def handle(self, *args, **options):
        created = bill_subscriptions()
        self.stdout.write(self.style.SUCCESS(f"Created {created} subscription charge(s)."))
