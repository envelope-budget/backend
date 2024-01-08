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
