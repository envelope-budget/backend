import io

from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db import models
from ofxparse import OfxParser

from budgetapp.utils import generate_uuid_hex
from budgets.models import Budget


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

    @classmethod
    def delete_unused_payees(cls, budget_id):
        """
        Hard deletes any payees that are not used in any transactions for the given budget.

        Args:
            budget_id (str): The ID of the budget to clean up payees for

        Returns:
            int: Number of payees deleted
        """
        # Get all payees for this budget
        payees = cls.objects.filter(budget_id=budget_id)

        # Get IDs of payees that are used in transactions
        used_payee_ids = (
            Transaction.objects.filter(budget_id=budget_id)
            .values_list("payee_id", flat=True)
            .distinct()
        )

        # Find payees that are not used in any transactions
        unused_payees = payees.exclude(id__in=used_payee_ids)

        # Count payees before deletion
        count = unused_payees.count()

        # Hard delete unused payees
        unused_payees.delete()

        return count


class TransactionManager(models.Manager):
    def get_queryset(self):
        # Default queryset will exclude deleted transactions and order by date descending
        return super().get_queryset().filter(deleted=False).order_by("-date")

    def include_deleted(self):
        # Include deleted transactions in the queryset
        return super().get_queryset().order_by("-date")


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
    pending = models.BooleanField(default=False)
    reconciled = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    import_id = models.CharField(max_length=255, blank=True, null=True)
    sfin_id = models.CharField(max_length=255, blank=True, null=True)
    import_payee_name = models.CharField(max_length=255, blank=True, null=True)
    deleted = models.BooleanField(default=False)

    objects = TransactionManager()

    def __str__(self):
        return f"{self.date} | {self.payee} | {self.amount}"

    # Override the save method
    def save(self, *args, **kwargs):
        if self.import_id:
            # Check if a transaction with the same budget, account, and import_id/sfin_id already exists
            if (
                Transaction.objects.filter(
                    budget=self.budget,
                    account=self.account,
                )
                .filter(
                    models.Q(import_id=self.import_id) | models.Q(sfin_id=self.sfin_id)
                )
                .exclude(id=self.id)
                .exists()
            ):

                raise ValidationError(
                    f"A transaction with import_id '{self.import_id}' already exists for this budget and account."
                )

        soft_delete = kwargs.pop("soft_delete", False)
        if not soft_delete:
            is_new = kwargs.get("force_insert", False)
            if not is_new:
                # Fetch the old transaction to get the old amount
                old_transaction = Transaction.objects.get(pk=self.pk)

                if old_transaction.envelope:
                    if old_transaction.envelope == self.envelope:
                        self.envelope.balance -= old_transaction.amount
                    else:
                        # If the envelope has changed, update the old envelope balance
                        old_transaction.envelope.balance -= old_transaction.amount
                        old_transaction.envelope.save()

                if self.account != old_transaction.account:
                    # If the account has changed, update the old account balance
                    old_transaction.account.balance -= old_transaction.amount
                    old_transaction.account.save()
                else:
                    self.account.balance -= old_transaction.amount

            # Update the balance for new and updated transactions
            self.account.balance += self.amount
            self.account.save()

            if self.envelope:
                self.envelope.balance += self.amount
                self.envelope.save()
                self.envelope.category.update_balance()

        super(Transaction, self).save(*args, **kwargs)

    def soft_delete(self):
        # Update the balance for deleted transactions
        self.account.balance -= self.amount
        self.account.save()
        if self.envelope:
            self.envelope.balance -= self.amount
            self.envelope.save()
        self.deleted = True
        self.save(soft_delete=True)

    def delete(self, *args, **kwargs):
        # Update the balance for deleted transactions
        self.account.balance -= self.amount
        self.account.save()
        if self.envelope:
            self.envelope.balance -= self.amount
            self.envelope.save()
        super(Transaction, self).delete(*args, **kwargs)

    class Meta:
        # Define unique_together constraint
        unique_together = ("budget", "account", "import_id")

    @classmethod
    def import_ofx(cls, budget_id: str, account_id: str, ofx_data: str):
        """
        Imports OFX data into the budget and account specified and returns the IDs of the created transactions and duplicate transactions.

        :param budget_id: The ID of the budget.
        :type budget_id: str
        :param account_id: The ID of the account.
        :type account_id: str
        :param ofx_data: The OFX data to be imported.
        :type ofx_data: str
        :return: Dictionary with lists of created and duplicate transaction IDs
        """
        from accounts.models import Account

        budget = Budget.objects.get(id=budget_id)
        account = Account.objects.get(id=account_id, budget_id=budget_id)
        # Convert string data to a file-like object
        ofx_file = io.StringIO(ofx_data)

        # Parse the OFX data
        ofx = OfxParser.parse(ofx_file)

        created_transaction_ids = []  # Store the IDs of created transactions
        duplicate_transaction_ids = []  # Store the IDs of duplicate transactions

        # Iterate over account transactions
        for transaction in ofx.account.statement.transactions:
            # Check for existing transaction with the same import_id
            transaction_exists = (
                Transaction.objects.include_deleted()
                .filter(
                    budget=budget,
                    account=account,
                    import_id=transaction.id,
                )
                .first()
            )

            if transaction_exists:
                # If transaction exists, add its ID to duplicate_transaction_ids
                duplicate_transaction_ids.append(transaction_exists.id)
            else:
                # Create a new Transaction for each unique OFX transaction
                payee = None
                if transaction.payee:
                    payee = Payee.objects.get_or_create(
                        name=transaction.payee.title(), budget=budget
                    )[0]
                try:
                    new_transaction = Transaction.objects.create(
                        budget=budget,
                        account=account,
                        date=transaction.date,
                        amount=int(transaction.amount * 1000),
                        memo=transaction.memo,
                        payee=payee,
                        import_id=transaction.id,
                        import_payee_name=transaction.payee,
                        cleared=True,
                    )
                    created_transaction_ids.append(new_transaction.id)
                except ValidationError:
                    # Handle any validation error (e.g., from unique constraints)
                    continue

        # Close the file-like object
        ofx_file.close()

        return {
            "created_ids": created_transaction_ids,
            "duplicate_ids": duplicate_transaction_ids,
        }


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
