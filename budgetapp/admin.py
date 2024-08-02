from django.contrib import admin
from .models import UserProfile, APIKey


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "active_budget")
    raw_id_fields = ("user", "active_budget")


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("user", "key", "created_at", "is_active")
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__email", "key")
    raw_id_fields = ("user",)
    readonly_fields = ("key", "created_at")

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ("user",)
        return self.readonly_fields
