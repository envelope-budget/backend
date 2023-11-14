import uuid

from django.db import models


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
