from django.db import migrations, models
import django.db.models.deletion
import logging

logger = logging.getLogger(__name__)


def create_debt_envelopes_for_existing_accounts(apps, schema_editor):
    """
    Create debt envelopes for existing credit card and loan accounts.
    """
    Account = apps.get_model("accounts", "Account")
    Envelope = apps.get_model("envelopes", "Envelope")
    Category = apps.get_model("envelopes", "Category")

    debt_account_types = ["credit_card", "loan", "credit", "line_of_credit"]

    # Get all existing debt accounts
    debt_accounts = Account.objects.filter(
        type__iregex=r"^(" + "|".join(debt_account_types) + ")$", deleted=False
    )

    created_envelopes = 0

    for account in debt_accounts:
        # Get or create "Debt" category for this budget
        debt_category, category_created = Category.objects.get_or_create(
            budget=account.budget, name="Debt", defaults={"sort_order": 999}
        )

        if category_created:
            logger.info(f"Created 'Debt' category for budget {account.budget.name}")

        # Create the linked envelope
        envelope_name = f"{account.name} Payments"
        envelope = Envelope.objects.create(
            budget=account.budget,
            category=debt_category,
            name=envelope_name,
            balance=0,
            linked_account=account,
        )

        created_envelopes += 1
        logger.info(f"Created envelope '{envelope_name}' for account '{account.name}'")

    logger.info(
        f"Migration completed: Created {created_envelopes} debt payment envelopes"
    )


def reverse_create_debt_envelopes(apps, schema_editor):
    """
    Remove debt envelopes created by this migration.
    """
    Envelope = apps.get_model("envelopes", "Envelope")

    # Delete envelopes that have linked accounts
    deleted_count = Envelope.objects.filter(linked_account__isnull=False).delete()[0]
    logger.info(f"Removed {deleted_count} linked envelopes")


class Migration(migrations.Migration):

    dependencies = [
        (
            "accounts",
            "0007_account_sfin_last_imported_on",
        ),
        ("envelopes", "0003_envelope_monthly_budget_amount"),
    ]

    operations = [
        migrations.AddField(
            model_name="envelope",
            name="linked_account",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="linked_envelope",
                to="accounts.account",
            ),
        ),
        migrations.RunPython(
            create_debt_envelopes_for_existing_accounts, reverse_create_debt_envelopes
        ),
    ]
