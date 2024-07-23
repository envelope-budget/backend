from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

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
    slug = models.SlugField(max_length=255)
    type = models.CharField(max_length=255)
    on_budget = models.BooleanField(default=True)
    closed = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)
    balance = models.IntegerField(default=0)
    cleared_balance = models.PositiveIntegerField(default=0)
    last_reconciled_at = models.DateTimeField(blank=True, null=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ["budget", "slug"]

    def __str__(self):
        return str(self.name)


@receiver(pre_save, sender=Account)
def slugify_name(sender, instance, *args, **kwargs):
    if not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        n = 1
        while Account.objects.filter(budget=instance.budget, slug=slug).exists():
            slug = f"{base_slug}-{n}"
            n += 1
        instance.slug = slug
