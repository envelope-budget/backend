from django.contrib import admin

from .models import Payee, Transaction, SubTransaction, TransactionMerge


@admin.register(Payee)
class PayeeAdmin(admin.ModelAdmin):
    list_display = ("name", "budget")
    list_filter = ("budget",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "payee", "amount", "budget", "account", "deleted")
    list_filter = ("budget", "account", "deleted")

    def get_queryset(self, request):
        # Use the include_deleted method to show all transactions
        return Transaction.objects.include_deleted()


@admin.register(SubTransaction)
class SubTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction", "envelope", "amount")
    list_filter = ("transaction", "envelope")


@admin.register(TransactionMerge)
class TransactionMergeAdmin(admin.ModelAdmin):
    list_display = ("id", "budget", "merged_transaction")
    list_filter = ("budget",)
