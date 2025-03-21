from decimal import Decimal
import logging
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
import requests

from budgetapp.utils import money_db_prep
from budgets.models import Budget
from envelopes.models import Category, Envelope

from .forms import AccountForm
from .models import Account, SimpleFINConnection

logger = logging.getLogger(__name__)


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
def x_add_sfin(request):
    if request.method == "POST":
        setup_token = request.POST.get("setup_token")
        if setup_token:
            try:
                # Store the SimpleFIN setup token associated with the user/budget
                SimpleFINConnection.create_from_setup_token(
                    budget=Budget.objects.get(id=request.session.get("budget")),
                    setup_token=setup_token,
                )
                messages.success(request, "SimpleFIN connection added successfully")
                return redirect(request.META.get("HTTP_REFERER"))
            except Exception as e:
                messages.error(request, f"Failed to add SimpleFIN connection: {str(e)}")
                return redirect(request.META.get("HTTP_REFERER"))

    # Get sfin access token
    try:
        sfin_connection = SimpleFINConnection.objects.get(
            budget=Budget.objects.get(id=request.session.get("budget"))
        )

        # Get accounts from SimpleFIN
        # accounts = sfin_connection.get_accounts()
        # logger.info("Accounts: %s", accounts)

        # Just render the form. It will load the accounts via ajax

        return render(
            request,
            "accounts/_add_sfin_account.html",
            {"sfin_connection": sfin_connection},
        )
    except SimpleFINConnection.DoesNotExist:
        sfin_connection = None

    return render(
        request, "accounts/_add_sfin.html", {"sfin_connection": sfin_connection}
    )


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
    _account = Account.objects.get(slug=slug, budget=request.session.get("budget"))
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
        {"categorized_envelopes": categorized_envelopes, "account": _account},
    )
    response.set_cookie("budget_id", request.session.get("budget"))
    response.set_cookie("account_id", _account.id)
    return response


def edit_account_form(request, account_id):
    """
    View to render the account edit form or process the form submission
    """
    user = request.user
    _account = get_object_or_404(Account, id=account_id)

    # Ensure the account belongs to a budget owned by the user
    if _account.budget.user != user:
        return HttpResponseForbidden("You don't have permission to edit this account")

    if request.method == "POST":
        # Process form submission
        name = request.POST.get("name")
        slug = request.POST.get("slug")
        account_type = request.POST.get("type")
        balance = request.POST.get("balance")
        description = request.POST.get("description", "")

        # Validate slug uniqueness
        if (
            slug != _account.slug
            and Account.objects.filter(budget=_account.budget, slug=slug).exists()
        ):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "An account with this slug already exists in this budget.",
                }
            )

        # Update account
        _account.name = name
        _account.slug = slug  # Add this line to update the slug
        _account.type = account_type
        if balance:
            _account.balance = Decimal(balance) * 1000
        _account.description = description
        _account.save()

        return JsonResponse({"status": "success"})

    # Render the form with account data
    return render(request, "accounts/_edit_account_form.html", {"account": _account})
