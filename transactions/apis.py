import io
from datetime import date
from typing import List, Optional

from django.shortcuts import get_object_or_404
from ninja import File, Router, Schema, UploadedFile
from ninja.pagination import paginate
from ninja.security import django_auth

from .models import Payee, Transaction, SubTransaction
from accounts.models import Account
from budgets.models import Budget
from envelopes.models import Envelope

router = Router()


class PayeeSchema(Schema):
    id: str
    name: str


class EnvelopeSchema(Schema):
    id: str
    name: str


class AccountSchema(Schema):
    id: str
    name: str


class TransactionSchema(Schema):
    id: str
    budget_id: str
    account: AccountSchema
    payee: Optional[PayeeSchema]
    import_payee_name: Optional[str]
    envelope: Optional[EnvelopeSchema]
    date: date
    amount: int
    memo: Optional[str]
    cleared: bool
    reconciled: bool
    approved: bool


class TransactionPatchSchema(Schema):
    budget_id: Optional[str] = None
    account_id: Optional[str] = None
    payee_id: Optional[str] = None
    envelope_id: Optional[str] = None
    date: Optional[date] = None
    amount: Optional[int] = None
    memo: Optional[str] = None
    cleared: Optional[bool] = None
    reconciled: Optional[bool] = None
    approved: Optional[bool] = None


class SubTransactionSchema(Schema):
    id: str
    transaction_id: str
    envelope_id: Optional[str]
    amount: int
    memo: Optional[str]


class OFXDataSchema(Schema):
    ofx_data: str


class BulkDeleteSchema(Schema):
    transaction_ids: List[str]


@router.get(
    "/{budget_id}",
    response=List[TransactionSchema],
    auth=django_auth,
    tags=["Transactions"],
)
@paginate
def list_transactions(request, budget_id: str):
    """List all transactions with pagination"""
    # TODO: ensure the budget belongs to the user
    transactions_query = Transaction.objects.filter(budget_id=budget_id)
    return transactions_query


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
    # TODO: ensure the transaction belongs to the user
    transaction = get_object_or_404(Transaction, id=transaction_id, budget_id=budget_id)
    return TransactionSchema.from_orm(transaction)


@router.post(
    "/{budget_id}", response=TransactionSchema, auth=django_auth, tags=["Transactions"]
)
def create_transaction(request, budget_id: str, transaction: TransactionSchema):
    """Create a new transaction"""
    # TODO: ensure the budget belongs to the user
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
    request, budget_id: str, transaction_id: str, transaction_data: TransactionSchema
):
    """
    Update a transaction with the given `transaction_id` and `budget_id`, ensuring it belongs to the user.
    """
    # Ensure the transaction belongs to the authenticated user
    trans = get_object_or_404(
        Transaction, id=transaction_id, budget_id=budget_id, budget__user=request.user
    )

    # Update transaction fields
    for attr, value in transaction_data.dict().items():
        setattr(trans, attr, value)
    trans.save()
    return TransactionSchema.from_orm(trans)


@router.patch(
    "/{budget_id}/{transaction_id}",
    response=TransactionSchema,
    auth=django_auth,
    tags=["Transactions"],
)
def patch_transaction(
    request,
    budget_id: str,
    transaction_id: str,
    transaction_data: TransactionPatchSchema,
):
    """
    Partially update a transaction with the given `transaction_id` and `budget_id`.
    """
    # Ensure the transaction belongs to the authenticated user
    trans = get_object_or_404(
        Transaction, id=transaction_id, budget_id=budget_id, budget__user=request.user
    )

    # Update specified transaction fields
    for attr, value in transaction_data.dict(exclude_unset=True).items():
        setattr(trans, attr, value)
    trans.save()
    return TransactionSchema.from_orm(trans)


@router.delete("/{budget_id}/{transaction_id}", auth=django_auth, tags=["Transactions"])
def delete_transaction(request, budget_id: str, transaction_id: str):
    """
    Delete a transaction.
    """
    # TODO: ensure the transaction belongs to the user
    transaction = get_object_or_404(Transaction, id=transaction_id, budget_id=budget_id)
    transaction.delete()
    return {"detail": "Transaction deleted successfully"}


@router.delete("/bulk-delete/{budget_id}", auth=django_auth, tags=["Transactions"])
def delete_transactions_bulk(request, budget_id: str, data: BulkDeleteSchema):
    """
    Delete multiple transactions in bulk. Ensures that both the budget and the transactions belong to the authenticated user.
    """
    # Verify that the budget belongs to the authenticated user
    if not Budget.objects.filter(id=budget_id, user=request.user).exists():
        return {"detail": "Budget not found or access denied"}, 404

    # Filter transactions by the provided IDs, the budget_id, and ensure they belong to the user
    transactions = Transaction.objects.filter(
        id__in=data.transaction_ids, budget_id=budget_id, budget__user=request.user
    )

    # Check if all transactions exist and belong to the user
    if transactions.count() != len(data.transaction_ids):
        return {"detail": "One or more transactions not found or access denied"}, 404

    # Delete the transactions
    transactions.delete()

    return {"detail": f"{transactions.count()} transactions deleted successfully"}


@router.post(
    "/{budget_id}/{account_id}/import/ofx/file", auth=django_auth, tags=["Transactions"]
)
def import_ofx_file(
    request, budget_id: str, account_id: str, ofx_file: UploadedFile = File(...)
):
    """Import transactions from an OFX file"""
    # TODO: ensure the account belongs to the user
    # Read the OFX file content
    ofx_data = ofx_file.file.read().decode("utf-8")

    # Call the class method to import transactions
    return Transaction.import_ofx(budget_id, account_id, ofx_data)


@router.post(
    "/{budget_id}/{account_id}/import/ofx/data", auth=django_auth, tags=["Transactions"]
)
def import_ofx_data(request, budget_id: str, account_id: str, data: OFXDataSchema):
    """Import transactions from an OFX data string"""
    # TODO: ensure the account belongs to the user
    # Call the class method to import transactions
    return Transaction.import_ofx(budget_id, account_id, data.ofx_data)
