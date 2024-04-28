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


class EnvelopeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(deleted=True).order_by("sort_order")


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
    deleted = models.BooleanField(default=False)

    objects = EnvelopeManager()

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.category:
            self.category.update_balance()
        super().save(*args, **kwargs)


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
