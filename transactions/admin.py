from django.contrib import admin

from .models import Payee, Transaction, SubTransaction


@admin.register(Payee)
class PayeeAdmin(admin.ModelAdmin):
    list_display = ("name", "budget")
    list_filter = ("budget",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "amount", "budget", "account")
    list_filter = ("budget", "account")


@admin.register(SubTransaction)
class SubTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction", "envelope", "amount")
    list_filter = ("transaction", "envelope")
