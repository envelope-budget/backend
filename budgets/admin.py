from django.contrib import admin

from .models import Budget


class BudgetAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    list_filter = ("user",)


admin.site.register(Budget, BudgetAdmin)
