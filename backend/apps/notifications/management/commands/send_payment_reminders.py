from django.core.management.base import BaseCommand

from apps.notifications.reminders import send_payment_reminders


class Command(BaseCommand):
    help = "Send due-soon and overdue payment reminders. Run once a day (cron / scheduler)."

    def handle(self, *args, **options):
        counts = send_payment_reminders()
        self.stdout.write(self.style.SUCCESS(
            f"Reminders sent: {counts['due_soon']} due soon, {counts['overdue']} overdue "
            f"({counts['skipped']} skipped, {counts['emails_failed']} emails failed)."
        ))
