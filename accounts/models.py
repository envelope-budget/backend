from django.db import models

from budgetapp.utils import generate_uuid_hex


class Account(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    on_budget = models.BooleanField(default=True)
    closed = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)
    balance = models.IntegerField(default=0)
    cleared_balance = models.PositiveIntegerField(default=0)
    last_reconciled_at = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)
