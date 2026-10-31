"""
Seed realistic sample data for local development and GUI review.

Creates (all idempotent, safe to run twice):
  - users: cegres1@hotmail.com (superuser + admin), admin@abem.test, admin2@abem.test,
    owner@abem.test and five more owners, all with the same password
  - three buildings: "Nile Tower" (admin@abem.test, co-admin cegres1), "Garden Residence"
    (cegres1) and "Palm Court" (admin2, there to prove tenant isolation)
  - units, default expense categories, costs, monthly subscriptions, payments (some units
    paid, some partial, some overdue), a pending InstaPay claim and a building asset

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --password 'Other@123'
    python manage.py seed_demo_data --reset      # delete the seeded users/buildings first
"""

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.apartments.models import Apartment, ApartmentStatus, UnitType
from apps.authentication.models import User, UserRole
from apps.buildings.models import Building, BuildingCoAdmin, UserBuilding
from apps.expenses.management.commands.seed_expense_categories import \
    DEFAULT_CATEGORIES
from apps.expenses.models import (Expense, ExpenseCategory, ExpenseKind,
                                  SplitType)
from apps.expenses.utils import run_split_engine
from apps.payments.allocation import auto_allocate, record_allocations
from apps.payments.models import (AssetType, BuildingAsset, Payment,
                                  PaymentClaim, PaymentMethod)

DEFAULT_PASSWORD = "P@ssw0rd"

ADMINS = [
    ("cegres1@hotmail.com", "Shehab", "El-Adl", True),
    ("admin@abem.test", "Amr", "Hassan", False),
    ("admin2@abem.test", "Laila", "Mansour", False),
]
OWNERS = [
    ("owner@abem.test", "Omar", "Khaled"),
    ("owner2@abem.test", "Mona", "Saeed"),
    ("owner3@abem.test", "Youssef", "Nabil"),
    ("owner4@abem.test", "Hana", "Fathy"),
    ("owner5@abem.test", "Karim", "Adel"),
    ("owner6@abem.test", "Salma", "Ragab"),
]
BUILDINGS = [
    # name, address, city, admin email, floors, apartments, stores
    ("Nile Tower", "12 Corniche El Nil St", "Cairo", "admin@abem.test", 4, 12, 2),
    ("Garden Residence", "5 Road 9, Maadi", "Cairo", "cegres1@hotmail.com", 3, 9, 0),
    ("Palm Court", "88 Palm Hills Ave", "Giza", "admin2@abem.test", 2, 6, 0),
]
# (title, category, amount, months ago)
COSTS = [
    ("Elevator service contract", "Elevator", Decimal("3200"), 2),
    ("Stairwell cleaning", "Cleaning", Decimal("1500"), 2),
    ("Electricity - common areas", "Utilities", Decimal("2750"), 1),
    ("Security guard salary", "Security", Decimal("4000"), 1),
    ("Water pump repair", "Plumbing", Decimal("1850"), 0),
]
# building name -> (plan code, days until paid_until); varied so the platform table shows different states
PLANS = {
    "Nile Tower": ("plus", 60),
    "Garden Residence": ("standard", -3),  # just lapsed: in the grace period
    "Palm Court": ("free", 365),
}
SUBSCRIPTION_AMOUNT = Decimal("500")
SEED_EMAILS = [a[0] for a in ADMINS] + [o[0] for o in OWNERS]


def months_ago(n):
    today = date.today().replace(day=1)
    year, month = today.year, today.month - n
    while month < 1:
        month += 12
        year -= 1
    return date(year, month, 1)


class Command(BaseCommand):
    help = "Seed sample users, buildings, units, expenses and payments for development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help="Password for every seeded user",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously seeded buildings and users first",
        )
        parser.add_argument(
            "--force", action="store_true", help="Allow running with DEBUG off"
        )

    def handle(self, *args, **opts):
        if not settings.DEBUG and not opts["force"]:
            raise CommandError(
                "Refusing to seed with DEBUG off (looks like production). Use --force to override."
            )
        self.password = opts["password"]
        with transaction.atomic():
            if opts["reset"]:
                self.reset()
            users = self.create_users()
            for index, spec in enumerate(BUILDINGS):
                self.create_building(spec, users, index)
        self.stdout.write(self.style.SUCCESS("Sample data ready."))
        self.stdout.write(f"  Password for every user: {self.password}")
        for email, *_ in ADMINS:
            self.stdout.write(f"  admin : {email}")
        for email, *_ in OWNERS:
            self.stdout.write(f"  owner : {email}")

    # ── helpers ──────────────────────────────────────────────────────────────

    def reset(self):
        names = [b[0] for b in BUILDINGS]
        # Payments are PROTECT-linked to reversals, so remove them explicitly first
        Payment.objects.filter(
            apartment__building__name__in=names, reversal_of__isnull=False
        ).delete()
        Payment.objects.filter(apartment__building__name__in=names).delete()
        # Expenses PROTECT their category, so they go before the building's categories do
        Expense.objects.filter(building__name__in=names).delete()
        Building.objects.filter(name__in=names).delete()
        User.objects.filter(email__in=SEED_EMAILS).delete()
        self.stdout.write("  Removed previously seeded data.")

    def create_users(self):
        users = {}
        for email, first, last, superuser in ADMINS:
            users[email] = self.upsert_user(
                email, first, last, UserRole.ADMIN, superuser
            )
        for email, first, last in OWNERS:
            users[email] = self.upsert_user(email, first, last, UserRole.OWNER, False)
        return users

    def upsert_user(self, email, first, last, role, superuser):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": first, "last_name": last, "role": role},
        )
        user.set_password(self.password)
        user.role = role
        user.is_active = True
        user.is_staff = superuser
        user.is_superuser = superuser
        user.must_change_password = False
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()
        return user

    def create_building(self, spec, users, index):
        name, address, city, admin_email, floors, apts, stores = spec
        building, created = Building.objects.get_or_create(
            name=name,
            defaults={
                "address": address,
                "city": city,
                "country": "Egypt",
                "num_floors": floors,
                "num_apartments": apts,
                "num_stores": stores,
                "admin": users[admin_email],
                "instapay_address": f"{name.split()[0].lower()}@instapay",
            },
        )
        self.seed_plan(building)
        if not created and building.apartments.exists():
            self.stdout.write(f"  {name}: already seeded, skipping")
            return
        if name == "Nile Tower":
            BuildingCoAdmin.objects.get_or_create(
                user=users["cegres1@hotmail.com"], building=building
            )
        ExpenseCategory.objects.bulk_create(
            [
                ExpenseCategory(
                    building=building, name=n, description=d, icon=i, color=c
                )
                for n, d, i, c in DEFAULT_CATEGORIES
            ],
            ignore_conflicts=True,
        )
        units = self.create_units(building, users, floors, apts, stores, index)
        admin = users[admin_email]
        self.create_expenses(building, admin)
        self.create_payments(building, admin, units)
        self.create_extras(building, admin, units, index)
        self.stdout.write(f"  {name}: {len(units)} units seeded")

    def create_units(self, building, users, floors, apts, stores, index):
        owner_users = [users[o[0]] for o in OWNERS]
        units = []
        per_floor = max(1, -(-apts // floors))
        for n in range(apts):
            floor = n // per_floor + 1
            owner = (
                owner_users[(n + index) % len(owner_users)] if n % 4 != 3 else None
            )  # every 4th unit has no owner yet
            units.append(
                Apartment.objects.create(
                    building=building,
                    unit_number=f"{floor}0{n % per_floor + 1}",
                    floor=floor,
                    unit_type=UnitType.APARTMENT,
                    size_sqm=Decimal("90") + 5 * (n % 4),
                    owner=owner,
                    status=(
                        ApartmentStatus.OCCUPIED if owner else ApartmentStatus.VACANT
                    ),
                )
            )
        for n in range(stores):
            units.append(
                Apartment.objects.create(
                    building=building,
                    unit_number=f"S{n + 1}",
                    floor=0,
                    unit_type=UnitType.STORE,
                    size_sqm=Decimal("45"),
                    rate_factor=Decimal("1.50"),
                    owner=owner_users[n % len(owner_users)],
                )
            )
        for unit in units:
            if unit.owner:
                unit.owners.add(unit.owner)
                UserBuilding.objects.get_or_create(user=unit.owner, building=building)
        # the first owner of the first building is the board chair, for the board screens
        first = (
            UserBuilding.objects.filter(building=building).order_by("joined_at").first()
        )
        if first:
            first.board_role = "chair"
            first.save(update_fields=["board_role"])
        return units

    def create_expenses(self, building, admin):
        categories = {
            c.name: c for c in ExpenseCategory.objects.filter(building=building)
        }
        for ago in (3, 2, 1, 0):
            start = months_ago(ago)
            self.add_expense(
                building,
                admin,
                categories["Management"],
                f"Monthly subscription {start:%b %Y}",
                SUBSCRIPTION_AMOUNT * building.apartments.count(),
                start,
                ExpenseKind.SUBSCRIPTION,
            )
        for title, category, amount, ago in COSTS:
            self.add_expense(
                building,
                admin,
                categories[category],
                title,
                amount,
                months_ago(ago) + timedelta(days=9),
                ExpenseKind.COST,
            )

    def add_expense(self, building, admin, category, title, amount, when, kind):
        expense = Expense.objects.create(
            building=building,
            category=category,
            title=title,
            amount=amount,
            expense_date=when,
            due_date=when + timedelta(days=10),
            kind=kind,
            split_type=SplitType.EQUAL_ALL,
            created_by=admin,
        )
        run_split_engine(expense)
        return expense

    def create_payments(self, building, admin, units):
        """Units pay oldest-first: ~half in full, a quarter partly, the rest stay overdue."""
        today = date.today()
        for n, unit in enumerate(units):
            unit.refresh_from_db()
            if unit.balance <= 0 or n % 4 == 3:
                continue  # n % 4 == 3 stays fully unpaid (overdue)
            amount = (
                unit.balance
                if n % 4 in (0, 1)
                else (unit.balance / 2).quantize(Decimal("0.01"))
            )
            self.record_payment(unit, admin, amount, today - timedelta(days=3 + n))

    def record_payment(self, unit, admin, amount, paid_on):
        unit.balance -= amount
        before = unit.balance + amount
        unit.save(update_fields=["balance", "updated_at"])
        payment = Payment.objects.create(
            apartment=unit,
            amount_paid=amount,
            payment_method=PaymentMethod.CASH,
            payment_date=paid_on,
            balance_before=before,
            balance_after=unit.balance,
            recorded_by=admin,
            notes="Seed data",
        )
        record_allocations(payment, auto_allocate(unit, amount))
        return payment

    def create_extras(self, building, admin, units, index=0):
        unpaid = next((u for u in units if u.owner and u.balance > 0), None)
        if unpaid:
            PaymentClaim.objects.create(
                apartment=unpaid,
                amount=min(unpaid.balance, Decimal("500")),
                reference=f"IPN-SEED-{index + 1:04d}",
                created_by=unpaid.owner,
            )
        BuildingAsset.objects.create(
            building=building,
            name="Lobby generator",
            asset_type=AssetType.EQUIPMENT,
            acquisition_date=months_ago(6),
            acquisition_value=Decimal("18000"),
            created_by=admin,
        )

    def seed_plan(self, building):
        """Give the building a plan if the plan rows exist (they come from the plans data migration)."""
        from apps.plans.models import BuildingPlan, Plan

        code, days = PLANS.get(building.name, (None, 0))
        plan = Plan.objects.filter(code=code).first() if code else None
        if plan is None:
            return
        BuildingPlan.objects.update_or_create(
            building=building, defaults={"plan": plan, "paid_until": date.today() + timedelta(days=days)}
        )
