from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from budgetapp.utils import money_db_prep
from budgets.models import Budget

from .forms import AccountForm
from .models import Account


@login_required
def account(request):
    return render(request, "accounts/account.html")


@login_required
def x_add_account_form(request):
    if request.method == "POST":
        form = AccountForm(request.POST)

        _account = Account.objects.create(
            name=request.POST.get("name"),
            type=request.POST.get("type"),
            note=request.POST.get("note"),
            balance=money_db_prep(request.POST.get("balance")),
            budget=Budget.objects.get(id=request.session.get("budget")),
        )
        messages.success(request, f'Account "{_account.name}" added')

        return redirect(request.META.get("HTTP_REFERER"))
    else:
        form = AccountForm()

    return render(request, "accounts/_add_account_form.html", {"form": form})
