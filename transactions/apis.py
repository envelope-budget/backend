import io
from datetime import date
from typing import List, Optional

from django.shortcuts import get_object_or_404
from ninja import File, Router, Schema, UploadedFile
from ninja.security import django_auth

from .models import Payee, Transaction, SubTransaction
from accounts.models import Account
from budgets.models import Budget
from envelopes.models import Envelope

router = Router()


class PayeeSchema(Schema):
    id: str
    name: str


class TransactionSchema(Schema):
    id: str
    budget_id: str
    account_id: str
    payee: Optional[PayeeSchema]
    import_payee_name: Optional[str]
    envelope_id: Optional[str]
    date: date
    amount: int
    memo: Optional[str]
    cleared: bool
    reconciled: bool
    approved: bool


class SubTransactionSchema(Schema):
    id: str
    transaction_id: str
    envelope_id: Optional[str]
    amount: int
    memo: Optional[str]


class OFXDataSchema(Schema):
    ofx_data: str


@router.get(
    "/{budget_id}",
    response=List[TransactionSchema],
    auth=django_auth,
    tags=["Transactions"],
)
def list_transactions(request, budget_id: str):
    """List all transactions"""
    transactions = Transaction.objects.filter(budget_id=budget_id)
    return [TransactionSchema.from_orm(transaction) for transaction in transactions]


@router.get(
    "/{budget_id}/{transaction_id}",
    response=TransactionSchema,
    auth=django_auth,
    tags=["Transactions"],
)
def get_transaction(request, budget_id: str, transaction_id: str):
    """
    Retrieves a transaction by its ID and budget ID.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id, budget_id=budget_id)
    return TransactionSchema.from_orm(transaction)


@router.post(
    "/{budget_id}", response=TransactionSchema, auth=django_auth, tags=["Transactions"]
)
def create_transaction(request, budget_id: str, transaction: TransactionSchema):
    """Create a new transaction"""
    new_transaction = Transaction.objects.create(
        **transaction.dict(), budget_id=budget_id
    )
    return TransactionSchema.from_orm(new_transaction)


@router.put(
    "/{budget_id}/{transaction_id}",
    response=TransactionSchema,
    auth=django_auth,
    tags=["Transactions"],
)
def update_transaction(
    request, budget_id: str, transaction_id: str, transaction: TransactionSchema
):
    """
    Update a transaction with the given `transaction_id` and `budget_id`.
    """
    trans = get_object_or_404(Transaction, id=transaction_id, budget_id=budget_id)
    for attr, value in transaction.dict().items():
        setattr(trans, attr, value)
    trans.save()
    return TransactionSchema.from_orm(trans)


@router.delete("/{budget_id}/{transaction_id}", auth=django_auth, tags=["Transactions"])
def delete_transaction(request, budget_id: str, transaction_id: str):
    """
    Delete a transaction.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id, budget_id=budget_id)
    transaction.delete()
    return {"detail": "Transaction deleted successfully"}


@router.post(
    "/{budget_id}/{account_id}/import/ofx/file", auth=django_auth, tags=["Transactions"]
)
def import_ofx_file(
    request, budget_id: str, account_id: str, ofx_file: UploadedFile = File(...)
):
    """Import transactions from an OFX file"""
    # Read the OFX file content
    ofx_data = ofx_file.file.read().decode("utf-8")

    # Call the class method to import transactions
    return Transaction.import_ofx(budget_id, account_id, ofx_data)


@router.post(
    "/{budget_id}/{account_id}/import/ofx/data", auth=django_auth, tags=["Transactions"]
)
def import_ofx_data(request, budget_id: str, account_id: str, data: OFXDataSchema):
    """Import transactions from an OFX data string"""
    # Call the class method to import transactions
    return Transaction.import_ofx(budget_id, account_id, data.ofx_data)
