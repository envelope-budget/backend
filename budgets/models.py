import os

from django.db import models

from budgetapp.utils import generate_uuid_hex
from envelopes.apis import CategorySchema
from envelopes.models import Category


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

    def categorized_envelopes(self):
        categories = Category.objects.filter(budget=self)
        for category in categories:
            # Assuming envelopes is a method or a property
            category.envelopes = category.envelopes()
        return [CategorySchema.from_orm(category) for category in categories]
