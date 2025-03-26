import os
import logging

from django.db import models

from budgetapp.utils import generate_uuid_hex
from envelopes.apis import CategorySchema
from envelopes.models import Category

logger = logging.getLogger(__name__)

UNALLOCATED_FUNDS = "Unallocated Funds"


class Budget(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_uuid_hex,
        editable=False,
        max_length=32,
    )
    # pylint: disable=hard-coded-auth-user
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    date_format = models.CharField(
        max_length=255, default=os.environ.get("DEFAULT_DATE_FORMAT", "YYYY-MM-DD")
    )
    currency_iso_code = models.CharField(max_length=3, default="USD")
    currency_decimal_digits = models.PositiveSmallIntegerField(default=2)
    currency_decimal_separator = models.CharField(max_length=1, default=".")
    currency_symbol_first = models.BooleanField(default=True)
    currency_group_separator = models.CharField(max_length=1, default=",")
    currency_symbol = models.CharField(max_length=48, default="$")
    currency_display_symbol = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Create unallocated funds envelope for new budgets
        self.create_unallocated_funds_envelope()

    def create_unallocated_funds_envelope(self):
        """Create the special Unallocated Funds envelope for this budget."""
        from envelopes.models import Envelope

        logger.info("Creating Unallocated Funds envelope for budget %s", self.id)

        # Check if it already exists
        unallocated = (
            Envelope.objects.include_all()
            .filter(budget=self, name=UNALLOCATED_FUNDS)
            .first()
        )
        logger.debug("Unallocated envelope: %s", unallocated)

        if not unallocated:
            unallocated = Envelope.objects.create(
                budget=self,
                name=UNALLOCATED_FUNDS,
                sort_order=0,  # Put it at the top
                hidden=True,
                note="Special envelope for unallocated funds. Do not delete.",
            )
        return unallocated

    def unallocated_envelope(self):
        """Get the special Unallocated Funds envelope for this budget."""
        from envelopes.models import Envelope

        logger.info("Getting Unallocated Funds envelope for budget %s", self.id)
        unallocated_envelope = (
            Envelope.objects.include_all()
            .filter(budget=self, name=UNALLOCATED_FUNDS)
            .first()
        )
        if not unallocated_envelope:
            unallocated_envelope = self.create_unallocated_funds_envelope()

        logger.debug("Unallocated envelope: %s", unallocated_envelope)
        return unallocated_envelope

    def categorized_envelopes(self):
        categories = Category.objects.filter(budget=self)
        for category in categories:
            # Assuming envelopes is a method or a property
            category.envelopes = category.envelopes()
        return [CategorySchema.from_orm(category) for category in categories]
