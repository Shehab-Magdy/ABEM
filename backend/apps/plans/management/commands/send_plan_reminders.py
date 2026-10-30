from django.core.management.base import BaseCommand

from apps.plans.reminders import send_plan_reminders


class Command(BaseCommand):
    help = "Tell building admins their plan or trial is ending, and when billing stops. Run daily."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Sent {send_plan_reminders()} reminder(s)."))
