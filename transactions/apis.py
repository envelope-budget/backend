from uuid import UUID
from datetime import date
from typing import List, Optional

from ninja import Router, Schema
from ninja.security import django_auth

from .models import Payee, Transaction, SubTransaction
from accounts.models import Account
from budgets.models import Budget
from envelopes.models import Envelope

router = Router()


class PayeeSchema(Schema):
    id: UUID
    name: str


class TransactionSchema(Schema):
    id: UUID
    budget_id: UUID
    account_id: UUID
    payee_id: Optional[UUID]
    envelope_id: Optional[UUID]
    date: date
    amount: int
    memo: Optional[str]
    cleared: bool
    reconciled: bool
    approved: bool


class SubTransactionSchema(Schema):
    id: UUID
    transaction_id: UUID
    envelope_id: Optional[UUID]
    amount: int
    memo: Optional[str]


@router.get(
    "/{budget_id}",
    response=List[TransactionSchema],
    auth=django_auth,
    tags=["Transactions"],
)
def list_transactions(request, budget_id: UUID):
    """List all transactions"""
    pass


@router.get(
    "/{budget_id}/{transaction_id}",
    response=TransactionSchema,
    auth=django_auth,
    tags=["Transactions"],
)
def get_transaction(request, budget_id: UUID, transaction_id: UUID):
    """Get a transaction by ID"""
    pass


@router.post(
    "/{budget_id}", response=TransactionSchema, auth=django_auth, tags=["Transactions"]
)
def create_transaction(request, budget_id: UUID, transaction: TransactionSchema):
    """Create a new transaction"""
    pass


@router.put(
    "/{budget_id}/{transaction_id}",
    response=TransactionSchema,
    auth=django_auth,
    tags=["Transactions"],
)
def update_transaction(
    request, budget_id: UUID, transaction_id: UUID, transaction: TransactionSchema
):
    """Update an existing transaction"""
    pass


@router.delete("/{budget_id}/{transaction_id}", auth=django_auth, tags=["Transactions"])
def delete_transaction(request, budget_id: UUID, transaction_id: UUID):
    """Delete a transaction"""
    pass
