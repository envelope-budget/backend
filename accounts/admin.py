from django.contrib import admin

from .models import Account


class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "budget", "balance")
    list_filter = ("budget",)


admin.site.register(Account, AccountAdmin)
