from datetime import timezone
from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    active_budget = models.ForeignKey(
        "budgets.Budget", on_delete=models.SET_NULL, null=True
    )

    def __str__(self):
        return str(self.user)


import secrets


class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    termination_date = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"API Key for {self.user.username}"

    @property
    def is_active(self):
        return self.termination_date is None or self.termination_date > timezone.now()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_urlsafe(48)[:64]
        super().save(*args, **kwargs)

    @staticmethod
    def get_user_from_key(key):
        try:
            api_key = APIKey.objects.get(key=key)
            if api_key.is_active:
                return api_key.user
        except APIKey.DoesNotExist:
            pass
        return None

    @staticmethod
    def create_new_key(user, termination_date=None, note=None):
        new_key = APIKey(user=user, termination_date=termination_date, note=note)
        new_key.save()
        return new_key
