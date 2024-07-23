import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import requests

from budgetapp.utils import money_db_prep
from budgets.models import Budget
from envelopes.models import Category, Envelope

from .forms import AccountForm
from .models import Account


@login_required
def account(request):
    return render(request, "accounts/account.html")


@login_required
def exchange_plaid_token(request):
    public_token = request.POST.get("public_token")
    plaid_environment = os.environ.get("PLAID_ENVIRONMENT", "SANDBOX")
    plaid_href = os.environ.get(f"PLAID_{plaid_environment}_HREF")
    plaid_secret = os.environ.get(f"PLAID_{plaid_environment}_SECRET")
    endpoint = f"{plaid_href}/item/public_token/exchange"
    data = {
        "client_id": os.environ.get("PLAID_CLIENT_ID"),
        "secret": plaid_secret,
        "public_token": public_token,
    }
    response = requests.post(
        endpoint, headers={"Content-Type": "application/json"}, json=data, timeout=10
    )
    response_json = response.json()
    assert False, response_json

    if response.status_code != 200:
        messages.error(request, response_json["error_message"])
        return redirect("account")
    else:
        # TODO: Associate with the user account
        return "Exchange successful"


@login_required
def x_add_plaid(request):
    # Get a link token
    plaid_environment = os.environ.get("PLAID_ENVIRONMENT", "SANDBOX")
    plaid_href = os.environ.get(f"PLAID_{plaid_environment}_HREF")
    plaid_secret = os.environ.get(f"PLAID_{plaid_environment}_SECRET")
    endpoint = f"{plaid_href}/link/token/create"
    data = {
        "client_id": os.environ.get("PLAID_CLIENT_ID"),
        "secret": plaid_secret,
        "client_name": "Envelope Budget",
        "user": {"client_user_id": f"{request.user.id}"},
        "products": ["transactions"],
        "country_codes": ["US"],
        "language": "en",
        "webhook": "https://webhook.site/c08ebde0-fb95-42f1-8516-73bcd50f02ba",
        "redirect_uri": "https://envelopebudget.com/oauth.html",
    }
    response = requests.post(
        endpoint, headers={"Content-Type": "application/json"}, json=data, timeout=5
    )
    response_data = response.json()
    response_data["client_id"] = os.environ.get("PLAID_CLIENT_ID")
    # assert False, response_data
    return render(request, "accounts/_add_plaid.html", response_data)


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


@login_required
def account_transactions(request, slug):
    account = Account.objects.get(slug=slug)
    categories = Category.objects.filter(budget=request.session.get("budget"))
    categorized_envelopes = []
    for category in categories:
        categorized_envelopes.append(
            {
                "category": category,
                "envelopes": Envelope.objects.filter(category=category),
            }
        )

    response = render(
        request,
        "transactions/transactions.html",
        {"categorized_envelopes": categorized_envelopes, "account": account},
    )
    response.set_cookie("budget_id", request.session.get("budget"))
    response.set_cookie("account_id", account.id)
    return response
