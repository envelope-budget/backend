from uuid import UUID
from typing import List, Optional
from datetime import datetime

from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404

from .models import Account
from budgets.models import Budget

router = Router()


class AccountSchema(Schema):
    id: UUID
    budget_id: UUID
    name: str
    type: str
    on_budget: bool
    closed: bool
    note: str
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


@router.get(
    "/{budget_id}",
    response=List[AccountSchema],
    auth=django_auth,
    tags=["Accounts"],
)
def list_accounts(request, budget_id: UUID):
    user = request.auth
    budget = get_object_or_404(
        Budget, id=budget_id, user=user
    )  # Ensure the budget belongs to the user
    accounts = Account.objects.filter(budget=budget, deleted=False)
    return [AccountSchema.from_orm(account) for account in accounts]


@router.get(
    "/{budget_id}/{account_id}",
    response=AccountSchema,
    auth=django_auth,
    tags=["Accounts"],
)
def get_account(request, budget_id: UUID, account_id: UUID):
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
def create_account(request, budget_id: UUID, account_in: AccountCreateSchema):
    user = request.auth
    budget = get_object_or_404(
        Budget, id=budget_id, user=user
    )  # Ensure the budget belongs to the user
    account = Account.objects.create(**account_in.dict(), budget=budget)
    return AccountSchema.from_orm(account)
