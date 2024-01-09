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


class TransactionPostPatchSchema(Schema):
    account_id: Optional[str] = None
    payee: Optional[str] = None
    envelope_id: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[int] = None
    memo: Optional[str] = None
    cleared: Optional[bool] = False
    reconciled: Optional[bool] = False
    approved: Optional[bool] = True


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
    # Ensure the budget belongs to the authenticated user
    if not Budget.objects.filter(id=budget_id, user=request.user).exists():
        return (
            []
        )  # Return an empty list or raise an error if the budget does not belong to the user

    transactions_query = Transaction.objects.filter(budget_id=budget_id, deleted=False)
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
def create_transaction(
    request, budget_id: str, transaction: TransactionPostPatchSchema
):
    """Create a new transaction"""
    # Ensure the budget belongs to the user
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)

    account = get_object_or_404(Account, id=transaction.account_id)
    payee = Payee.objects.get_or_create(name=transaction.payee, budget=budget)[0]
    envelope = get_object_or_404(Envelope, id=transaction.envelope_id)
    new_transaction = Transaction.objects.create(
        budget=budget,
        account=account,
        envelope=envelope,
        payee=payee,
        date=transaction.date,
        amount=transaction.amount,
        memo=transaction.memo,
        cleared=transaction.cleared,
        reconciled=transaction.reconciled,
        approved=transaction.approved,
    )
    return TransactionSchema.from_orm(new_transaction)


@router.put(
    "/{budget_id}/{transaction_id}",
    response=TransactionSchema,
    auth=django_auth,
    tags=["Transactions"],
)
def update_transaction(
    request,
    budget_id: str,
    transaction_id: str,
    transaction_data: TransactionPostPatchSchema,
):
    """
    Update a transaction with the given `transaction_id` and `budget_id`, ensuring it belongs to the user.
    """
    # Ensure the transaction belongs to the authenticated user
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    trans = get_object_or_404(
        Transaction, id=transaction_id, budget_id=budget_id, budget__user=request.user
    )

    # Update transaction fields
    trans.account = get_object_or_404(Account, id=transaction_data.account_id)
    trans.payee = Payee.objects.get_or_create(
        name=transaction_data.payee, budget=budget
    )[0]
    if transaction_data.envelope_id is not None:
        trans.envelope = get_object_or_404(Envelope, id=transaction_data.envelope_id)
    else:
        trans.envelope = None
    trans.date = transaction_data.date
    trans.amount = transaction_data.amount
    trans.memo = transaction_data.memo
    trans.cleared = transaction_data.cleared
    trans.reconciled = transaction_data.reconciled
    trans.approved = transaction_data.approved
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
    transaction_data: TransactionPostPatchSchema,
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
    # Ensure the transaction belongs to the authenticated user
    transaction = get_object_or_404(
        Transaction, id=transaction_id, budget_id=budget_id, budget__user=request.user
    )

    # Mark the transaction as deleted
    transaction.deleted = True
    transaction.save()
    return {"detail": "Transaction deleted successfully"}


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
