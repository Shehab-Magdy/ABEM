from django.core.management.base import BaseCommand

from apps.governance.finalize import finalize_polls


class Command(BaseCommand):
    help = "Settle expense-approval polls whose voting time is up. Run daily."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Settled {finalize_polls()} poll(s)."))
