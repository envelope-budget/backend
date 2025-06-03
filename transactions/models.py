from datetime import timedelta
import io
import logging

from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.db import transaction as db_transaction
from django.db import models
from ofxparse import OfxParser

from budgetapp.utils import generate_uuid_hex
from budgets.models import Budget


logger = logging.getLogger(__name__)


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["budget", "name"],
                condition=models.Q(deleted=False),
                name="unique_budget_payee_name",
            )
        ]


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
    import_id = models.CharField(max_length=255, blank=True, null=True)
    sfin_id = models.CharField("SimpleFIN ID", max_length=255, blank=True, null=True)
    import_payee_name = models.CharField(max_length=255, blank=True, null=True)
    in_inbox = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    is_transfer = models.BooleanField(default=False)
    transfer_account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="transfer_transactions",
    )
    transfer_transaction = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="linked_transfer",
    )

    objects = TransactionManager()

    def __str__(self):
        return f"{self.date} | {self.payee} | {self.amount}"

    # Override the save method
    def save(self, *args, **kwargs):
        if self.import_id:
            # Check if a transaction with the same budget, account, and import_id already exists
            existing_query = Transaction.objects.filter(
                budget=self.budget,
                account=self.account,
                import_id=self.import_id,
            ).exclude(id=self.id)

            # Only check sfin_id if it's not None
            if self.sfin_id:
                existing_query = existing_query | Transaction.objects.filter(
                    budget=self.budget,
                    account=self.account,
                    sfin_id=self.sfin_id,
                ).exclude(id=self.id)

            if existing_query.exists():
                raise ValidationError(
                    f"A transaction with import_id '{self.import_id}' or sfin_id '{self.sfin_id}' already exists for this budget and account."
                )

        soft_delete = kwargs.pop("soft_delete", False)
        if not soft_delete:
            is_new = kwargs.get("force_insert", False)
            if not is_new:
                # Fetch the old transaction to get the old amount
                old_transaction = Transaction.objects.include_deleted().get(pk=self.pk)

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
                if self.envelope.category:
                    self.envelope.category.update_balance()

        super(Transaction, self).save(*args, **kwargs)

    def soft_delete(self):
        # Update the balance for deleted transactions
        self.account.balance -= self.amount
        self.account.save()
        logger.info(
            "Transaction Payee: %s; Account: %s Balance: %s",
            self.payee,
            self.account.name,
            self.account.balance,
        )
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
        constraints = [
            models.UniqueConstraint(
                fields=["budget", "account", "import_id"],
                condition=models.Q(deleted=False),
                name="unique_budget_account_import_id",
            ),
            models.UniqueConstraint(
                fields=["budget", "account", "sfin_id"],
                condition=models.Q(deleted=False),
                name="unique_budget_account_sfin_id",
            ),
        ]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["amount"]),
            models.Index(fields=["cleared"]),
            models.Index(fields=["in_inbox"]),
            models.Index(fields=["pending"]),
            models.Index(fields=["deleted"]),
        ]

    @classmethod
    def merge_transactions(cls, budget_id, transaction_ids):
        """
        Merge two or more transactions into a single transaction.

        Args:
            budget_id: The ID of the budget
            transaction_ids: List of transaction IDs to merge

        Returns:
            A tuple of (merged_transaction, merge_record)

        Raises:
            ValidationError: If transactions cannot be merged
        """

        if len(transaction_ids) < 2:
            raise ValidationError("At least two transactions are required for merging")

        # Get the transactions to merge
        transactions = list(
            cls.objects.filter(
                id__in=transaction_ids, budget_id=budget_id, deleted=False
            )
        )

        if len(transactions) != len(transaction_ids):
            raise ValidationError("One or more transactions not found")

        # Check if all transactions have the same account and amount
        first_transaction = transactions[0]
        account = first_transaction.account
        amount = first_transaction.amount

        for trans in transactions[1:]:
            if trans.account.id != account.id:
                raise ValidationError(
                    "Transactions must have the same account to merge"
                )
            if trans.amount != amount:
                raise ValidationError("Transactions must have the same amount to merge")

        # Determine the earliest date
        earliest_date = min(t.date for t in transactions)

        # Determine envelope (if they have different envelopes, return error)
        envelope = None
        for trans in transactions:
            if trans.envelope:
                if envelope and trans.envelope.id != envelope.id:
                    raise ValidationError(
                        "Transactions have different envelopes and cannot be merged"
                    )
                envelope = trans.envelope

        # Determine cleared status (if any is cleared, mark as cleared)
        cleared = any(t.cleared for t in transactions)

        # Determine pending status (if any is not pending, mark as not pending)
        pending = all(t.pending for t in transactions)

        # Determine reconciled status (if any is reconciled, mark as reconciled)
        reconciled = any(t.reconciled for t in transactions)

        # Determine in inbox status (if any is in inbox, mark as in inbox)
        in_inbox = any(t.in_inbox for t in transactions)

        # Determine sfin_id - prioritize the non-pending transaction's sfin_id
        sfin_id = None
        for trans in transactions:
            if trans.sfin_id and not trans.pending:
                sfin_id = trans.sfin_id
                break

        # If no non-pending transaction with sfin_id found, use the first available sfin_id
        if not sfin_id:
            for trans in transactions:
                if trans.sfin_id:
                    sfin_id = trans.sfin_id
                    break

        # Choose payee from user-entered transaction, fallback to first transaction
        payee = None
        for trans in transactions:
            if not trans.import_id and not trans.sfin_id:  # User-entered transaction
                payee = trans.payee
                break
        if (
            payee is None
        ):  # If no user-entered payee found, use first transaction's payee
            payee = first_transaction.payee

        # Prefer memo from user-entered (non-imported) transaction
        memo = None
        for trans in transactions:
            if not trans.import_id and not trans.sfin_id:  # User-entered transaction
                memo = trans.memo
                break
        if memo is None:  # If no user-entered memo found, use first transaction's memo
            memo = first_transaction.memo

        # Get the budget
        budget = Budget.objects.get(id=budget_id)

        # Use a database transaction to ensure atomicity
        with db_transaction.atomic():
            # Calculate the total amount to be removed from the account balance
            # (all transactions except one, since we'll be adding one back)
            total_amount_to_remove = amount * (len(transactions) - 1)

            # Update the account balance directly
            account.balance -= total_amount_to_remove
            account.save()

            logger.info(
                "Merge: Adjusted account %s balance by %s to %s",
                account.name,
                total_amount_to_remove,
                account.balance,
            )

            # If there's an envelope, update its balance too
            if envelope:
                envelope.balance -= total_amount_to_remove
                envelope.save()
                logger.info(
                    "Merge: Adjusted envelope %s balance by %s to %s",
                    envelope.name,
                    total_amount_to_remove,
                    envelope.balance,
                )

            # Mark original transactions as deleted without adjusting balances
            for trans in transactions:
                trans.deleted = True
                trans.save(
                    soft_delete=True
                )  # Use soft_delete flag to avoid balance adjustments
                logger.info("Merge: Marked transaction %s as deleted", trans.id)

            # Create the merged transaction without adjusting balances
            merged_transaction = cls(
                budget=budget,
                account=account,
                payee=payee,
                envelope=envelope,
                date=earliest_date,
                amount=amount,
                memo=memo,
                cleared=cleared,
                pending=pending,
                reconciled=reconciled,
                in_inbox=in_inbox,
                sfin_id=sfin_id,
            )
            # Save without adjusting balances (we've already done that manually)
            merged_transaction.save(soft_delete=True)
            logger.info("Merge: Created new transaction %s", merged_transaction.id)

            # Create the merge record
            merge = TransactionMerge.create_merge(
                budget=budget,
                merged_transaction=merged_transaction,
                source_transaction_ids=transaction_ids,
            )

        return merged_transaction, merge

    @classmethod
    def import_ofx(cls, budget_id: str, account_id: str, ofx_data: str):
        """
        Imports OFX data into the budget and account specified and returns the IDs of the
        created transactions and duplicate transactions.

        :param budget_id: The ID of the budget.
        :type budget_id: str
        :param account_id: The ID of the account.
        :type account_id: str
        :param ofx_data: The OFX data to be imported.
        :type ofx_data: str
        :return: Dictionary with lists of created and duplicate transaction IDs
        """
        # pylint: disable=import-outside-toplevel
        from accounts.models import Account
        import logging

        logger = logging.getLogger(__name__)

        logger.info(
            "Starting OFX import for budget %s, account %s", budget_id, account_id
        )

        budget = Budget.objects.get(id=budget_id)
        account = Account.objects.get(id=account_id, budget_id=budget_id)
        # Convert string data to a file-like object
        ofx_file = io.StringIO(ofx_data)

        # Parse the OFX data
        logger.debug("Parsing OFX data")
        ofx = OfxParser.parse(ofx_file)

        created_transaction_ids = []  # Store the IDs of created transactions
        duplicate_transaction_ids = []  # Store the IDs of duplicate transactions

        # Iterate over account transactions
        logger.info(
            "Processing %d transactions from OFX file",
            len(ofx.account.statement.transactions),
        )
        for transaction in ofx.account.statement.transactions:
            logger.debug("Processing transaction with ID: %s", transaction.id)
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
                logger.debug("Found duplicate transaction: %s", transaction_exists.id)
                duplicate_transaction_ids.append(transaction_exists.id)
            else:
                # Create a new Transaction for each unique OFX transaction
                payee = None
                if transaction.payee:
                    logger.debug(
                        "Creating/getting payee: %s", transaction.payee.title()
                    )
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
                        sfin_id=None,
                    )
                    logger.debug("Created new transaction: %s", new_transaction.id)
                    created_transaction_ids.append(new_transaction.id)
                except ValidationError as e:
                    # Handle any validation error (e.g., from unique constraints)
                    logger.error("Validation error creating transaction: %s", str(e))
                    continue

        # Close the file-like object
        ofx_file.close()

        logger.info(
            "OFX import completed. Created: %d, Duplicates: %d",
            len(created_transaction_ids),
            len(duplicate_transaction_ids),
        )

        return {
            "created_ids": created_transaction_ids,
            "duplicate_ids": duplicate_transaction_ids,
        }

    @classmethod
    def create_transfer(
        cls,
        budget,
        from_account,
        to_account,
        amount,
        date,
        memo="",
        payee_name="Transfer",
    ):
        """
        Create a transfer between two accounts.

        Args:
            budget: The budget instance
            from_account: Account to transfer from
            to_account: Account to transfer to
            amount: Amount to transfer (positive value)
            date: Date of transfer
            memo: Optional memo
            payee_name: Payee name for the transfer

        Returns:
            Tuple of (from_transaction, to_transaction)
        """
        from .models import Payee

        # Get or create transfer payee
        payee, _ = Payee.objects.get_or_create(name=payee_name, budget=budget)

        with db_transaction.atomic():
            # Create outflow transaction (from account)
            from_transaction = cls.objects.create(
                budget=budget,
                account=from_account,
                payee=payee,
                date=date,
                amount=-abs(amount),  # Negative for outflow
                memo=memo,
                is_transfer=True,
                transfer_account=to_account,
                cleared=True,
                in_inbox=False,
            )

            # Create inflow transaction (to account)
            to_transaction = cls.objects.create(
                budget=budget,
                account=to_account,
                payee=payee,
                date=date,
                amount=abs(amount),  # Positive for inflow
                memo=memo,
                is_transfer=True,
                transfer_account=from_account,
                cleared=True,
                in_inbox=False,
            )

            # Link the transactions
            from_transaction.transfer_transaction = to_transaction
            to_transaction.transfer_transaction = from_transaction
            from_transaction.save()
            to_transaction.save()

        return from_transaction, to_transaction

    def mark_as_transfer(self, transfer_account, create_counterpart=True):
        """
        Mark this transaction as a transfer and optionally create the counterpart.

        Args:
            transfer_account: The account this transfers to/from
            create_counterpart: Whether to create the counterpart transaction

        Returns:
            The counterpart transaction if created, None otherwise
        """
        with db_transaction.atomic():
            self.is_transfer = True
            self.transfer_account = transfer_account
            self.in_inbox = False

            counterpart = None
            if create_counterpart:
                # Create counterpart transaction
                counterpart = Transaction.objects.create(
                    budget=self.budget,
                    account=transfer_account,
                    payee=self.payee,
                    date=self.date,
                    amount=0 - self.amount,  # Opposite amount
                    memo=self.memo,
                    is_transfer=True,
                    transfer_account=self.account,
                    cleared=True,
                    in_inbox=False,
                )

                # Link them
                self.transfer_transaction = counterpart
                counterpart.transfer_transaction = self
                counterpart.save()

            self.save()

        return counterpart

    @classmethod
    def find_potential_transfer_matches(cls, transaction):
        """
        Find potential transfer matches for a transaction.

        Args:
            transaction: The transaction to find matches for

        Returns:
            QuerySet of potential matches
        """
        # Look for transactions with opposite amount, same date (±1 day), different account
        date_range_start = transaction.date - timedelta(days=1)
        date_range_end = transaction.date + timedelta(days=1)

        return cls.objects.filter(
            budget=transaction.budget,
            amount=-transaction.amount,
            date__range=[date_range_start, date_range_end],
            is_transfer=False,
            transfer_transaction__isnull=True,
        ).exclude(account=transaction.account)


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


class TransactionMerge(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE)
    merged_transaction = models.ForeignKey(
        "transactions.Transaction",
        on_delete=models.CASCADE,
        related_name="resulting_merge",
    )
    source_transactions = models.ManyToManyField(
        "transactions.Transaction", related_name="source_for_merges"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Merge {self.id} - Result: {self.merged_transaction.id}"

    @classmethod
    def create_merge(cls, budget, merged_transaction, source_transaction_ids):
        """
        Create a merge record and store the original transactions

        Args:
            budget: The budget the transactions belong to
            merged_transaction: The new transaction created from the merge
            source_transaction_ids: List of IDs of the original transactions

        Returns:
            The created TransactionMerge instance
        """
        # Create the merge record
        merge = cls.objects.create(budget=budget, merged_transaction=merged_transaction)

        # Get the source transactions and add them to the merge
        source_transactions = Transaction.objects.include_deleted().filter(
            id__in=source_transaction_ids
        )
        merge.source_transactions.add(*source_transactions)

        return merge

    def undo(self):
        """
        Undo this merge by restoring the original transactions and removing the merged one

        Returns:
            List of restored transaction IDs
        """
        # Get the source transactions
        # pylint: disable=no-member
        source_transactions = self.source_transactions.all()
        restored_ids = []

        # Restore each source transaction
        for transaction in source_transactions:
            transaction.deleted = False
            transaction.save(
                soft_delete=True
            )  # Use soft_delete=True to avoid balance recalculation
            restored_ids.append(transaction.id)

        # Delete the merged transaction
        self.merged_transaction.soft_delete()

        # Delete this merge record
        self.delete()

        return restored_ids
