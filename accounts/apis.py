from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from django.conf import settings
from django.db import DatabaseError
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.security import django_auth
from plaid.api import plaid_api
import plaid

from budgets.models import Budget
from .models import Account, SimpleFINConnection


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


class SimpleFINAccountSchema(Schema):
    """Schema for SimpleFIN account data to be added"""

    id: str
    type: str = "account"


class AddSimpleFINAccountsRequest(Schema):
    """Request schema for adding SimpleFIN accounts"""

    accounts: List[SimpleFINAccountSchema]
    sfinData: Dict[str, Any]


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


@router.post(
    "/{budget_id}/simplefin/add-accounts",
    response=Dict[str, Any],
    auth=django_auth,
    tags=["Accounts"],
)
def add_simplefin_accounts(request, budget_id: str, data: AddSimpleFINAccountsRequest):
    """
    Add selected SimpleFIN accounts to the budget.

    Takes a list of SimpleFIN account IDs with their types and creates
    corresponding Account objects in the database.

    Args:
        budget_id: The ID of the budget to add accounts to
        data: Contains accounts to add and the full SimpleFIN data

    Returns:
        Dictionary with results of the account creation process
    """
    user = request.auth
    budget = get_object_or_404(Budget, id=budget_id, user=user)

    # Get or create SimpleFIN connection
    try:
        connection = SimpleFINConnection.objects.get(budget=budget)
    except SimpleFINConnection.DoesNotExist:
        return {
            "error": "No SimpleFIN connection exists for this budget",
            "accounts_added": 0,
        }

    results = {"success": True, "accounts_added": 0, "accounts": [], "errors": []}

    # Process each selected account
    for account_data in data.accounts:
        try:
            # Import the account using the connection's import_account method
            account = connection.import_account(
                data.sfinData, account_data.id, account_type=account_data.type
            )

            if isinstance(account, dict) and "error" in account:
                # Handle error case
                results["errors"].append(
                    {"account_id": account_data.id, "error": account["error"]}
                )
                continue

            # Add the created account to results
            results["accounts"].append(
                {
                    "id": account.id,
                    "name": account.name,
                    "type": account.type,
                    "balance": account.balance,
                    "sfin_id": account.sfin_id,
                }
            )
            results["accounts_added"] += 1

        except (ValueError, TypeError, AttributeError, KeyError) as e:
            logger.error(
                "Error importing SimpleFIN account %s: %s", account_data.id, str(e)
            )
            results["errors"].append({"account_id": account_data.id, "error": str(e)})

    # Update success flag if any errors occurred
    if results["errors"]:
        results["success"] = False

    return results


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
        import_transactions: Whether to import the transactions to a matching EB account
            (defaults to True)

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


@router.post(
    "/{budget_id}/archive/{account_id}",
    response=Dict[str, Any],
    auth=django_auth,
    tags=["Accounts"],
)
def archive_account(request, budget_id: str, account_id: str):
    """
    Archive an account by setting its 'closed' field to True.

    Args:
        budget_id: The ID of the budget
        account_id: The ID of the account to archive

    Returns:
        Dictionary with status and message
    """
    user = request.auth
    get_object_or_404(
        Budget, id=budget_id, user=user
    )  # Ensure the budget belongs to the user

    try:
        account = get_object_or_404(
            Account, id=account_id, budget_id=budget_id, deleted=False
        )

        # Set the account as closed
        account.closed = True
        account.save()

        return {
            "status": "success",
            "message": f"Account '{account.name}' has been archived successfully.",
        }
    except (Account.DoesNotExist, ValidationError, DatabaseError) as e:
        logger.error("Error archiving account %s: %s", account_id, str(e))
        return {"status": "error", "message": f"Failed to archive account: {str(e)}"}
