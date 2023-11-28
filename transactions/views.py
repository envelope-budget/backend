from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def transactions(request):
    return render(request, "transactions/transactions.html")
