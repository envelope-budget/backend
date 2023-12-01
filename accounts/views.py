from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import AccountForm


@login_required
def account(request):
    return render(request, "accounts/account.html")


@login_required
def x_add_account_form(request):
    if request.method == "POST":
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/")
    else:
        form = AccountForm()

    return render(request, "accounts/_add_account_form.html", {"form": form})
