from django.contrib import admin
from .models import UserProfile, APIKey


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "active_budget")
    raw_id_fields = ("user", "active_budget")


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "obfuscated_key",
        "created_at",
        "termination_date",
        "is_active_emoji",
    )
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__email", "key")
    readonly_fields = ("obfuscated_key", "created_at", "key", "id")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("user",)
        return self.readonly_fields

    def obfuscated_key(self, obj):
        if obj.key:
            return f"{obj.key[:4]}...{obj.key[-4:]}"
        return ""

    obfuscated_key.short_description = "Key"

    def is_active_emoji(self, obj):
        return "✅" if obj.is_active else "❌"

    is_active_emoji.short_description = "Is Active"
