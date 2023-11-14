import uuid

from django.db import models


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=99)
    hidden = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "categories"


class Envelope(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE)
    category = models.ForeignKey(
        "envelopes.Category", blank=True, null=True, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=99)
    balance = models.PositiveIntegerField(default=0)
    hidden = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)


class EnvelopeGoal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
