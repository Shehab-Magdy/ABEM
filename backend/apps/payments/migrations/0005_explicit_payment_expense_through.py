# Manual migration: convert auto M2M (payments_payment_expenses)
# to explicit through model PaymentExpense with allocated_amount.

import django.db.models.deletion
from django.db import migrations, models


def forwards_copy_m2m(apps, schema_editor):
    """Copy rows from the auto-generated M2M table into the new through table."""
    db = schema_editor.connection.alias
    PaymentExpense = apps.get_model("payments", "PaymentExpense")
    # The auto table name for `Payment.expenses` is `payments_payment_expenses`
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT payment_id, expense_id FROM payments_payment_expenses"
        )
        rows = cursor.fetchall()
    objs = [
        PaymentExpense(payment_id=payment_id, expense_id=expense_id, allocated_amount=None)
        for payment_id, expense_id in rows
    ]
    PaymentExpense.objects.using(db).bulk_create(objs, ignore_conflicts=True)


def backwards_copy_m2m(apps, schema_editor):
    """Copy rows back from PaymentExpense into the auto M2M table."""
    PaymentExpense = apps.get_model("payments", "PaymentExpense")
    with schema_editor.connection.cursor() as cursor:
        for pe in PaymentExpense.objects.all():
            cursor.execute(
                "INSERT OR IGNORE INTO payments_payment_expenses (payment_id, expense_id) VALUES (%s, %s)",
                [str(pe.payment_id), str(pe.expense_id)],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("expenses", "0003_add_category_parent"),
        ("payments", "0004_remove_asset_current_value"),
    ]

    operations = [
        # 1. Create the explicit through table
        migrations.CreateModel(
            name="PaymentExpense",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "allocated_amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Amount of the payment allocated to this expense. NULL = legacy/unspecified.",
                        max_digits=10,
                        null=True,
                    ),
                ),
                (
                    "expense",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment_expenses",
                        to="expenses.expense",
                    ),
                ),
                (
                    "payment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment_expenses",
                        to="payments.payment",
                    ),
                ),
            ],
            options={
                "unique_together": {("payment", "expense")},
            },
        ),
        # 2. Copy existing M2M data
        migrations.RunPython(forwards_copy_m2m, backwards_copy_m2m),
        # 3. Remove the old auto M2M field
        migrations.RemoveField(
            model_name="payment",
            name="expenses",
        ),
        # 4. Re-add the M2M field with the explicit through model
        migrations.AddField(
            model_name="payment",
            name="expenses",
            field=models.ManyToManyField(
                blank=True,
                related_name="payments",
                through="payments.PaymentExpense",
                to="expenses.expense",
            ),
        ),
    ]
