from decimal import Decimal
import datetime
import logging
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect

from plaid import Environment
from plaid.api import plaid_api
from plaid.api_client import ApiClient
from plaid.configuration import Configuration
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_get_request import TransactionsGetRequest

from budgetapp.utils import money_db_prep
from budgets.models import Budget
from envelopes.models import Category, Envelope
from .forms import AccountForm
from .models import Account, SimpleFINConnection

logger = logging.getLogger(__name__)


# Initialize Plaid client
def get_plaid_client():
    plaid_environment = os.environ.get("PLAID_ENVIRONMENT", "sandbox").lower()
    client_id = os.environ.get("PLAID_CLIENT_ID")

    # Try to get the secret with the expected naming pattern
    secret = os.environ.get(f"PLAID_{plaid_environment.upper()}_SECRET")

    # Debug logging
    logger.info(f"Plaid Environment: {plaid_environment}")
    logger.info(f"Client ID: {client_id}")
    logger.info(f"Looking for secret key: PLAID_{plaid_environment.upper()}_SECRET")
    logger.info(f"Secret exists: {bool(secret)}")

    if not client_id:
        raise ValueError("PLAID_CLIENT_ID environment variable is not set")
    if not secret:
        raise ValueError(
            f"PLAID_{plaid_environment.upper()}_SECRET environment variable is not set"
        )

    if plaid_environment == "sandbox":
        host = Environment.Sandbox
    elif plaid_environment == "production":
        host = Environment.Production
    else:
        host = Environment.Sandbox

    configuration = Configuration(
        host=host,
        api_key={
            "clientId": client_id,
            "secret": secret,
        },
    )
    api_client = ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


@login_required
def account(request):
    return render(request, "accounts/account.html")


@login_required
def exchange_plaid_token(request):
    public_token = request.POST.get("public_token")

    try:
        client = get_plaid_client()
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response["access_token"]
        item_id = exchange_response["item_id"]

        # Get account information
        accounts_request = AccountsGetRequest(access_token=access_token)
        accounts_response = client.accounts_get(accounts_request)

        # Create Account records for each Plaid account
        budget = Budget.objects.get(id=request.session.get("budget"))

        for plaid_account in accounts_response["accounts"]:
            # Check if account already exists
            existing_account = Account.objects.filter(
                budget=budget, plaid_account_id=plaid_account["account_id"]
            ).first()

            if not existing_account:
                Account.objects.create(
                    name=plaid_account["name"],
                    type=plaid_account["type"],
                    balance=money_db_prep(
                        str(plaid_account["balances"]["current"] or 0)
                    ),
                    budget=budget,
                    plaid_access_token=access_token,
                    plaid_account_id=plaid_account["account_id"],
                    plaid_item_id=item_id,
                    plaid_account_type=plaid_account["type"],
                    plaid_account_subtype=plaid_account.get("subtype", ""),
                    plaid_official_name=plaid_account.get("official_name", ""),
                    plaid_mask=plaid_account.get("mask", ""),
                )

        messages.success(request, "Plaid accounts connected successfully!")
        return redirect("account")

    except Exception as e:
        logger.error(f"Plaid token exchange error: {str(e)}")
        messages.error(request, f"Failed to connect Plaid account: {str(e)}")
        return redirect("account")


@login_required
def x_add_plaid(request):
    try:
        client = get_plaid_client()

        link_request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="Envelope Budget",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(request.user.id)),
            webhook="https://webhook.site/c08ebde0-fb95-42f1-8516-73bcd50f02ba",
            redirect_uri="https://envelopebudget.com/oauth.html",
        )

        response = client.link_token_create(link_request)
        link_token = response["link_token"]

        context = {
            "link_token": link_token,
            "client_id": os.environ.get("PLAID_CLIENT_ID"),
            "environment": os.environ.get("PLAID_ENVIRONMENT", "sandbox"),
        }

        return render(request, "accounts/_add_plaid.html", context)

    except Exception as e:
        logger.error(f"Plaid link token creation error: {str(e)}")
        messages.error(request, f"Failed to initialize Plaid connection: {str(e)}")
        return redirect("account")


@login_required
def sync_plaid_transactions(request, account_id):
    """
    Sync transactions for a specific Plaid account
    """
    try:
        account = get_object_or_404(
            Account, id=account_id, budget=request.session.get("budget")
        )

        if not account.plaid_access_token:
            return JsonResponse(
                {"status": "error", "message": "Account is not connected to Plaid"}
            )

        client = get_plaid_client()

        # Get transactions from the last 30 days
        start_date = datetime.date.today() - datetime.timedelta(days=30)
        end_date = datetime.date.today()

        transactions_request = TransactionsGetRequest(
            access_token=account.plaid_access_token,
            start_date=start_date,
            end_date=end_date,
            account_ids=[account.plaid_account_id],
        )

        transactions_response = client.transactions_get(transactions_request)

        # Process transactions (you'll need to create Transaction model and logic)
        transaction_count = len(transactions_response["transactions"])

        return JsonResponse(
            {"status": "success", "message": f"Synced {transaction_count} transactions"}
        )

    except Exception as e:
        logger.error(f"Plaid transaction sync error: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)})


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
        _account.slug = slug
        _account.type = account_type
        if balance:
            _account.balance = Decimal(balance) * 1000
        _account.description = description
        _account.save()

        return JsonResponse({"status": "success"})

    # Render the form with account data
    return render(request, "accounts/_edit_account_form.html", {"account": _account})
