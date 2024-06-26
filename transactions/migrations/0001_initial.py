# Generated by Django 5.0 on 2024-01-12 23:05

import budgetapp.utils
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("budgets", "0001_initial"),
        ("envelopes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payee",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=budgetapp.utils.generate_uuid_hex,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("deleted", models.BooleanField(default=False)),
                (
                    "budget",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="budgets.budget"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=budgetapp.utils.generate_uuid_hex,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("date", models.DateField()),
                ("amount", models.IntegerField()),
                ("memo", models.TextField(blank=True, max_length=1023, null=True)),
                ("cleared", models.BooleanField(default=False)),
                ("reconciled", models.BooleanField(default=False)),
                ("approved", models.BooleanField(default=False)),
                ("import_id", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "import_payee_name",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("deleted", models.BooleanField(default=False)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.account",
                    ),
                ),
                (
                    "budget",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="budgets.budget"
                    ),
                ),
                (
                    "envelope",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="envelopes.envelope",
                    ),
                ),
                (
                    "payee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.payee",
                    ),
                ),
            ],
            options={
                "unique_together": {("budget", "account", "import_id")},
            },
        ),
        migrations.CreateModel(
            name="SubTransaction",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=budgetapp.utils.generate_uuid_hex,
                        editable=False,
                        max_length=32,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("amount", models.IntegerField()),
                ("memo", models.TextField(blank=True, max_length=1023, null=True)),
                ("deleted", models.BooleanField(default=False)),
                (
                    "envelope",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="envelopes.envelope",
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.transaction",
                    ),
                ),
            ],
        ),
    ]
