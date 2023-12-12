from django.db import models

from budgetapp.utils import generate_uuid_hex


class Payee(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)


class Transaction(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE)
    account = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    payee = models.ForeignKey(
        "transactions.Payee", on_delete=models.CASCADE, blank=True, null=True
    )
    envelope = models.ForeignKey(
        "envelopes.Envelope", on_delete=models.CASCADE, blank=True, null=True
    )
    date = models.DateField()
    amount = models.IntegerField()
    memo = models.TextField(blank=True, null=True, max_length=1023)
    cleared = models.BooleanField(default=False)
    reconciled = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    import_id = models.CharField(max_length=255, blank=True, null=True)
    import_payee_name = models.CharField(max_length=255, blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} | {self.payee} | {self.amount}"


class SubTransaction(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    transaction = models.ForeignKey(
        "transactions.Transaction", on_delete=models.CASCADE
    )
    envelope = models.ForeignKey(
        "envelopes.Envelope", on_delete=models.CASCADE, blank=True, null=True
    )
    amount = models.IntegerField()
    memo = models.TextField(blank=True, null=True, max_length=1023)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.transaction} | {self.envelope} | {self.amount}"
