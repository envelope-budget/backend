from django.db import models

from budgetapp.utils import generate_uuid_hex


class CategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(deleted=True).order_by("sort_order")


class Category(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    balance = models.IntegerField(default=0)
    sort_order = models.IntegerField(default=99)
    hidden = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    objects = CategoryManager()

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "categories"

    def envelopes(self):
        return Envelope.objects.filter(category=self)

    def update_balance(self):
        self.balance = sum([envelope.balance for envelope in self.envelopes()])
        self.save()

    def delete(self, using=None, keep_parents=False):
        """
        Override delete to prevent deletion if category contains envelopes.
        """
        if self.envelopes().filter(deleted=False).exists():
            from django.core.exceptions import ValidationError

            raise ValidationError(
                f"Cannot delete category '{self.name}' because it contains envelopes. "
                "Please move or delete the envelopes first."
            )
        return super().delete(using=using, keep_parents=keep_parents)


class EnvelopeManager(models.Manager):
    def get_queryset(self):
        # Exclude deleted envelopes and the special Unallocated Funds envelope
        return (
            super()
            .get_queryset()
            .exclude(deleted=True)
            .exclude(name="Unallocated Funds")
            .order_by("sort_order")
        )

    def include_deleted(self):
        """Return a queryset that includes deleted envelopes but still excludes Unallocated Funds."""
        return super().get_queryset().exclude(name="Unallocated Funds")

    def include_all(self):
        """Return a queryset that includes all envelopes including deleted and Unallocated Funds."""
        return super().get_queryset()

    def get_unallocated_funds(self, budget):
        """Get the Unallocated Funds envelope for a budget."""
        return (
            super()
            .get_queryset()
            .filter(budget=budget, name="Unallocated Funds")
            .first()
        )


class Envelope(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE)
    category = models.ForeignKey(
        "envelopes.Category", blank=True, null=True, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=99)
    balance = models.IntegerField(default=0)
    note = models.TextField(blank=True, null=True)
    hidden = models.BooleanField(default=False)
    monthly_budget_amount = models.IntegerField(
        default=0, help_text="Planned monthly allocation amount"
    )
    deleted = models.BooleanField(default=False)
    linked_account = models.OneToOneField(
        "accounts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_envelope",
    )

    objects = EnvelopeManager()

    def __str__(self):
        return str(self.name)

    @classmethod
    def transfer(cls, amount, source, destination):
        """
        Transfer money between envelopes.
        Args:
            amount: Integer amount to transfer
            source: Source Envelope instance
            destination: Destination Envelope instance
        """
        source.balance -= amount
        destination.balance += amount

        source.save()
        destination.save()

    def delete(self, *args, **kwargs):
        """Override delete to prevent deletion of Unallocated Funds envelope."""
        if self.name == "Unallocated Funds":
            # Just mark as hidden instead of deleting
            self.hidden = True
            self.save()
            return

        # Store the category before deletion to update its balance after
        category = self.category

        # For regular envelopes, proceed with normal deletion

        super().delete(*args, **kwargs)

        # Update category balance after deletion
        if category:
            category.update_balance()

    def save(self, *args, **kwargs):
        # Check if this is an update and if the category or balance changed
        old_category = None
        if self.pk:
            try:
                old_envelope = Envelope.objects.get(pk=self.pk)
                old_category = old_envelope.category
            except Envelope.DoesNotExist:
                pass

        # Save the envelope first
        super().save(*args, **kwargs)

        # Update the current category balance
        if self.category:
            self.category.update_balance()

        # If the envelope moved to a different category, update the old category too
        if old_category and old_category != self.category:
            old_category.update_balance()


class EnvelopeGoal(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    envelope = models.ForeignKey("envelopes.Envelope", on_delete=models.CASCADE)
    type = models.CharField(max_length=255)
    day = models.PositiveIntegerField(blank=True, null=True)
    cadence = models.CharField(max_length=255, blank=True, null=True)
    cadence_frequency = models.PositiveSmallIntegerField(blank=True, null=True)
    creation_month = models.PositiveSmallIntegerField(blank=True, null=True)
    target_amount = models.PositiveIntegerField(blank=True, null=True)
    target_month = models.PositiveSmallIntegerField(blank=True, null=True)
    percentage_completed = models.PositiveSmallIntegerField(blank=True, null=True)
    months_to_budget = models.PositiveSmallIntegerField(blank=True, null=True)
    under_funded = models.PositiveIntegerField(blank=True, null=True)
    overall_funded = models.PositiveIntegerField(blank=True, null=True)
    overall_left = models.PositiveIntegerField(blank=True, null=True)
