"""
clear_db.py — Wipe all operational data while preserving the superuser.

Deleted:
  - All audit logs
  - All notifications
  - All payments and asset sales / assets
  - All apartment expenses, recurring configs, media files, expenses
  - All apartments and UserBuilding records
  - All buildings  (cascades → expense categories)
  - All non-superuser users

Preserved:
  - The superuser account (password is reset and printed)
  - A JSON snapshot of every expense category is saved to
    expense_categories_backup.json before deletion.

Run from the backend directory:
    python clear_db.py
"""

import json
import os
import sys

# Ensure the backend package root is on the path when running from repo root
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.apps import apps

from apps.authentication.models import User
from apps.buildings.models import Building
from apps.expenses.models import ExpenseCategory

SEP = "─" * 60


def banner(text):
    print(f"\n{SEP}\n  {text}\n{SEP}")


# ── 1. Back up expense categories ─────────────────────────────────────────────

banner("Backing up expense categories")
categories = list(
    ExpenseCategory.objects.select_related("building", "parent").values(
        "name", "description", "icon", "color",
        "building__name", "parent__name", "is_active",
    )
)
backup_path = os.path.join(os.path.dirname(__file__), "expense_categories_backup.json")
with open(backup_path, "w", encoding="utf-8") as f:
    json.dump(categories, f, indent=2, default=str)
print(f"  Saved {len(categories)} categories → {backup_path}")

# ── 2. Audit logs ──────────────────────────────────────────────────────────────

banner("Deleting audit logs")
n, _ = apps.get_model("audit", "AuditLog").objects.all().delete()
print(f"  Deleted {n} audit log(s)")

# ── 3. Notifications ───────────────────────────────────────────────────────────

banner("Deleting notifications")
n, _ = apps.get_model("notifications", "Notification").objects.all().delete()
print(f"  Deleted {n} notification(s)")

# ── 4. Payments + assets ───────────────────────────────────────────────────────

banner("Deleting payments and assets")
n, _ = apps.get_model("payments", "AssetSale").objects.all().delete()
print(f"  Deleted {n} asset sale(s)")
n, _ = apps.get_model("payments", "BuildingAsset").objects.all().delete()
print(f"  Deleted {n} building asset(s)")
n, _ = apps.get_model("payments", "Payment").objects.all().delete()
print(f"  Deleted {n} payment(s)")

# ── 5. Expenses ────────────────────────────────────────────────────────────────

banner("Deleting expenses")
n, _ = apps.get_model("expenses", "ApartmentExpense").objects.all().delete()
print(f"  Deleted {n} apartment expense share(s)")
n, _ = apps.get_model("expenses", "RecurringConfig").objects.all().delete()
print(f"  Deleted {n} recurring config(s)")
n, _ = apps.get_model("expenses", "MediaFile").objects.all().delete()
print(f"  Deleted {n} media file record(s)")
n, _ = apps.get_model("expenses", "Expense").objects.all().delete()
print(f"  Deleted {n} expense(s)")

# ── 6. Buildings (cascades → apartments, UserBuilding, categories) ─────────────

banner("Deleting buildings (cascades to apartments and expense categories)")
n, details = Building.objects.all().delete()
print(f"  Deleted {n} object(s): {details}")

# ── 7. Non-superuser users ─────────────────────────────────────────────────────

banner("Deleting non-superuser users")
n, _ = User.objects.filter(is_superuser=False).delete()
print(f"  Deleted {n} user(s)")

# ── 8. Reset superuser password and print credentials ─────────────────────────

banner("Superuser credentials")
superuser = User.objects.filter(is_superuser=True).first()
if superuser:
    new_password = "Admin@12345"
    superuser.set_password(new_password)
    superuser.failed_login_attempts = 0
    superuser.locked_until = None
    superuser.save(update_fields=["password", "failed_login_attempts", "locked_until"])
    print(f"  Email   : {superuser.email}")
    print(f"  Password: {new_password}")
else:
    print("  WARNING: No superuser found in the database!")

# ── 9. Summary ─────────────────────────────────────────────────────────────────

banner("Done")
print(f"  Expense category backup → {backup_path}")
print("  Re-create buildings to get fresh default categories.")
print(SEP)
