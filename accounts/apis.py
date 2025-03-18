from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from ninja import Router, Schema
from ninja.security import django_auth
from django.conf import settings
from django.shortcuts import get_object_or_404
import plaid
from plaid.api import plaid_api

from .models import Account, SimpleFINConnection
from budgets.models import Budget


logger = logging.getLogger(__name__)


router = Router()

# Plaid configuration
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        "clientId": settings.PLAID_CLIENT_ID,
        "secret": settings.PLAID_SECRET,
    },
)

# Create an instance of the API client
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)


class AccountSchema(Schema):
    id: str
    budget_id: str
    name: str
    type: str
    on_budget: bool
    closed: bool
    note: Optional[str] = None
    balance: int
    cleared_balance: int
    deleted: bool
    last_reconciled_at: Optional[datetime] = None


class AccountCreateSchema(Schema):
    name: str
    type: str
    on_budget: bool = True
    closed: bool = False
    note: str = ""
    balance: int = 0
    cleared_balance: int = 0
    # last_reconciled_at is omitted since it's likely set when reconciling, not on create
    # deleted is omitted because it defaults to False and typically wouldn't be set on create


class SimpleFINConnectionSchema(Schema):
    """
    SimpleFINConnectionSchema represents the schema for a simple financial connection.

    Attributes:
        id (str): The unique identifier for the financial connection.
        budget_id (str): The identifier for the associated budget.
        access_url (str): The URL used to access the financial connection.
        created_at (datetime): The timestamp when the financial connection was created.
    """

    id: str
    budget_id: str
    access_url: str
    created_at: datetime


@router.get(
    "/{budget_id}",
    response=List[AccountSchema],
    tags=["Accounts"],
)
def list_accounts(request, budget_id: str):
    user = request.auth
    budget = get_object_or_404(
        Budget, id=budget_id, user=user
    )  # Ensure the budget belongs to the user
    accounts = Account.objects.filter(budget=budget, deleted=False)
    return [AccountSchema.from_orm(account) for account in accounts]


@router.get(
    "/{budget_id}/simplefin",
    response=Optional[SimpleFINConnectionSchema],
    auth=django_auth,
    tags=["Accounts"],
)
def get_simplefin_connection(request, budget_id: str):
    """
    Get the SimpleFIN connection information for a budget.
    Returns None if no connection exists.
    """
    user = request.auth

    budget = get_object_or_404(
        Budget, id=budget_id, user=user
    )  # Ensure the budget belongs to the user

    try:
        connection = SimpleFINConnection.objects.get(budget=budget)
        return SimpleFINConnectionSchema(
            id=connection.id,
            budget_id=str(budget.id),
            access_url=connection.access_url,
            created_at=connection.created_at,
        )
    except SimpleFINConnection.DoesNotExist:
        return None


@router.get(
    "/{budget_id}/simplefin/accounts",
    response=Dict[str, Any],
    auth=django_auth,
    tags=["Accounts"],
)
def get_simplefin_accounts(request, budget_id: str):
    """
    Get the accounts from the SimpleFIN connection for a budget.
    """
    user = request.auth

    budget = get_object_or_404(Budget, id=budget_id, user=user)

    try:
        connection = SimpleFINConnection.objects.get(budget=budget)
        return connection.get_accounts()
    except SimpleFINConnection.DoesNotExist:
        return None


@router.get(
    "/{budget_id}/simplefin/transactions",
    response=Dict[str, Any],
    auth=django_auth,
    tags=["Accounts"],
)
def get_simplefin_transactions(
    request,
    budget_id: str,
    account_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_pending: bool = True,
    import_transactions: bool = True,
):
    """
    Get transactions from the SimpleFIN connection for a budget.

    Args:
        budget_id: The ID of the budget
        account_id: Optional specific account to retrieve transactions for
        start_date: Optional start date for transaction filtering in 'YYYY-MM-DD' format
        end_date: Optional end date for transaction filtering in 'YYYY-MM-DD' format
        include_pending: Whether to include pending transactions (defaults to True)
        import_transactions: Whether to import the transactions to a matching EB account (defaults to True)

    Returns:
        JSON response containing transaction details from the SimpleFIN API
    """
    user = request.auth
    budget = get_object_or_404(Budget, id=budget_id, user=user)

    try:
        connection = SimpleFINConnection.objects.get(budget=budget)
        result = connection.get_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            include_pending=include_pending,
            import_transactions=import_transactions,
        )

        # Check if there was an error in the result
        if "error" in result:
            logger.error("SimpleFIN API error: %s", result["error"])
            return result

        return result
    except SimpleFINConnection.DoesNotExist:
        return {"error": "No SimpleFIN connection exists for this budget"}
    except (ValueError, KeyError, AttributeError) as e:
        logger.error("Unexpected error in get_simplefin_transactions: %s", str(e))
        return {"error": f"Failed to retrieve transactions: {str(e)}"}


@router.get(
    "/{budget_id}/{account_id}",
    response=AccountSchema,
    auth=django_auth,
    tags=["Accounts"],
)
def get_account(request, budget_id: str, account_id: str):
    user = request.auth
    get_object_or_404(
        Budget, id=budget_id, user=user
    )  # Ensure the budget belongs to the user
    account = get_object_or_404(
        Account, id=account_id, budget_id=budget_id, deleted=False
    )
    return AccountSchema.from_orm(account)


@router.post(
    "/{budget_id}", response=AccountSchema, auth=django_auth, tags=["Accounts"]
)
def create_account(request, budget_id: str, account_in: AccountCreateSchema):
    user = request.auth
    budget = get_object_or_404(
        Budget, id=budget_id, user=user
    )  # Ensure the budget belongs to the user
    account = Account.objects.create(**account_in.dict(), budget=budget)
    return AccountSchema.from_orm(account)
