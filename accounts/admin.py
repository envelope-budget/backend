from django.contrib import admin

from .models import Account, SimpleFINConnection


class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "budget", "balance")
    list_filter = ("budget",)


class SimpleFINConnectionAdmin(admin.ModelAdmin):
    list_display = ("budget", "created_at")
    list_filter = ("budget",)


admin.site.register(Account, AccountAdmin)
admin.site.register(SimpleFINConnection, SimpleFINConnectionAdmin)
