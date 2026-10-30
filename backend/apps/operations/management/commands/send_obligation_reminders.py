from django.core.management.base import BaseCommand

from apps.operations.services import send_obligation_reminders


class Command(BaseCommand):
    help = "Remind admins and the board about obligations coming due and contracts ending. Run daily."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Sent {send_obligation_reminders()} reminder(s)."))
