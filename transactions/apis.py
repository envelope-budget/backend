from datetime import date, datetime
from typing import List, Optional
import logging

from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from django.shortcuts import get_object_or_404
from ninja import File, Router, Schema, UploadedFile
from ninja.pagination import paginate
from ninja.security import django_auth

from accounts.models import Account
from budgets.models import Budget
from envelopes.models import Envelope
from transactions.search import parse_search_query
from .models import Payee, Transaction, TransactionMerge


logger = logging.getLogger(__name__)
router = Router()


class PayeeSchema(Schema):
    id: str
    name: str


class PayeeCreateSchema(Schema):
    name: str


class PayeeUpdateSchema(Schema):
    name: str
    deleted: bool = False


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
    pending: bool
    reconciled: bool
    import_id: Optional[str]
    sfin_id: Optional[str]


class TransactionPostPatchSchema(Schema):
    account_id: Optional[str] = None
    payee: Optional[str] = None
    envelope_id: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[int] = None
    memo: Optional[str] = None
    cleared: Optional[bool] = False
    reconciled: Optional[bool] = False
    import_id: Optional[str] = None
    in_inbox: Optional[bool] = None


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


class Error(Schema):
    message: str


@router.get(
    "/transactions/{budget_id}",
    response=List[TransactionSchema],
    tags=["Transactions"],
)
@paginate
def list_transactions(
    request,
    budget_id: str,
    account_id: Optional[str] = None,
    in_inbox: Optional[bool] = None,
    search: Optional[str] = None,
):
    """
    List all transactions with pagination.

    Supports filtering by account, inbox status, and search query.
    """
    # Ensure the budget belongs to the authenticated user
    if not Budget.objects.filter(id=budget_id, user=request.user).exists():
        return []  # Return an empty list if the budget does not belong to the user

    # Start with base query
    transactions_query = Transaction.objects.filter(budget_id=budget_id, deleted=False)

    # Apply search filter if provided
    if search:
        search_filter = parse_search_query(search, budget_id)
        transactions_query = transactions_query.filter(search_filter)
    # Only apply in_inbox filter if search is not provided or if explicitly requested
    elif in_inbox is not None:
        transactions_query = transactions_query.filter(in_inbox=in_inbox)

    # Apply account filter if provided
    if account_id:
        transactions_query = transactions_query.filter(account_id=account_id)

    # Order by date descending
    transactions_query = transactions_query.order_by("-date")

    return transactions_query


@router.post(
    "/transactions/{budget_id}/archive",
    response={200: dict, 400: Error},
    tags=["Transactions"],
)
def archive_transactions(request, budget_id: str, transaction_ids: BulkDeleteSchema):
    """Archive multiple transactions by their IDs"""
    # Ensure the budget belongs to the user
    get_object_or_404(Budget, id=budget_id, user=request.user)

    try:
        # Update all matching transactions that belong to this budget
        updated = Transaction.objects.filter(
            id__in=transaction_ids.transaction_ids, budget_id=budget_id, deleted=False
        ).update(in_inbox=False)

        return {"archived_count": updated}
    except (Transaction.DoesNotExist, ValueError, DatabaseError) as e:
        return 400, {"message": f"Failed to archive transactions: {str(e)}"}


class TransactionMergeRequest(Schema):
    transaction_ids: List[str]


class TransactionMergeResponse(Schema):
    merged_transaction: TransactionSchema
    merge_id: str
    source_transaction_ids: List[str]


class MergeError(Schema):
    message: str


@router.post(
    "/transactions/{budget_id}/merge",
    response={200: TransactionMergeResponse, 400: MergeError},
    tags=["Transactions"],
)
def merge_transactions(request, budget_id: str, merge_data: TransactionMergeRequest):
    """
    Merge two or more transactions into a single transaction.

    Transactions must have the same account and amount to be merged.
    """
    logger.info("Merging transactions: %s", merge_data.transaction_ids)

    # Ensure the budget belongs to the user
    get_object_or_404(Budget, id=budget_id, user=request.user)

    try:
        # Use the model method to perform the merge
        merged_transaction, merge = Transaction.merge_transactions(
            budget_id=budget_id, transaction_ids=merge_data.transaction_ids
        )

        return {
            "merged_transaction": TransactionSchema.from_orm(merged_transaction),
            "merge_id": merge.id,
            "source_transaction_ids": merge_data.transaction_ids,
        }
    except ValidationError as e:
        return 400, {
            "message": str(e.messages[0] if isinstance(e.messages, list) else str(e))
        }


class TransactionMergeSchema(Schema):
    id: str
    merged_transaction: TransactionSchema
    source_transactions: List[TransactionSchema]
    created_at: datetime


@router.get(
    "/transactions/{budget_id}/merges/{merge_id}",
    response={200: TransactionMergeSchema, 404: Error},
    tags=["Transactions"],
)
def get_transaction_merge(request, budget_id: str, merge_id: str):
    """
    Get details of a transaction merge, including the source transactions.
    """
    # Ensure the budget belongs to the user
    get_object_or_404(Budget, id=budget_id, user=request.user)

    # Get the merge record
    merge = get_object_or_404(TransactionMerge, id=merge_id, budget_id=budget_id)

    # Get the source transactions (including deleted ones)
    source_transactions = merge.source_transactions.all()

    return {
        "id": merge.id,
        "merged_transaction": TransactionSchema.from_orm(merge.merged_transaction),
        "source_transactions": [
            TransactionSchema.from_orm(t) for t in source_transactions
        ],
        "created_at": merge.created_at,
    }


@router.post(
    "/transactions/{budget_id}/merges/{merge_id}/undo",
    response={200: dict, 404: Error},
    tags=["Transactions"],
)
def undo_transaction_merge(request, budget_id: str, merge_id: str):
    """
    Undo a transaction merge, restoring the original transactions.
    """
    # Ensure the budget belongs to the user
    get_object_or_404(Budget, id=budget_id, user=request.user)

    # Get the merge record
    merge = get_object_or_404(TransactionMerge, id=merge_id, budget_id=budget_id)

    # Undo the merge
    restored_ids = merge.undo()

    return {
        "message": "Merge successfully undone",
        "restored_transaction_ids": restored_ids,
    }


@router.get(
    "/transactions/{budget_id}/merges",
    response=List[TransactionMergeSchema],
    tags=["Transactions"],
)
def list_transaction_merges(request, budget_id: str):
    """
    List all transaction merges for a budget.
    """
    # Ensure the budget belongs to the user
    get_object_or_404(Budget, id=budget_id, user=request.user)

    # Get all merge records for this budget
    merges = TransactionMerge.objects.filter(budget_id=budget_id)

    return [
        {
            "id": merge.id,
            "merged_transaction": TransactionSchema.from_orm(merge.merged_transaction),
            "source_transactions": [
                TransactionSchema.from_orm(t) for t in merge.source_transactions.all()
            ],
            "created_at": merge.created_at,
        }
        for merge in merges
    ]


@router.get(
    "/transactions/{budget_id}/{transaction_id}",
    response=TransactionSchema,
    tags=["Transactions"],
)
def get_transaction(request, budget_id: str, transaction_id: str):
    """
    Retrieves a transaction by its ID and budget ID.
    """
    # ensure the transaction belongs to the user
    transaction = get_object_or_404(Transaction, id=transaction_id, budget_id=budget_id)
    return TransactionSchema.from_orm(transaction)


def get_or_create_payee(name: str, budget: Budget) -> Payee:
    """
    Helper function to get or create a payee, handling the case where
    multiple payees with the same name exist (including deleted ones).
    """
    try:
        # First try to get an active (non-deleted) payee
        return Payee.objects.get(name=name, budget=budget, deleted=False)
    except Payee.DoesNotExist:
        # If no active payee exists, create a new one
        return Payee.objects.create(name=name, budget=budget, deleted=False)
    except Payee.MultipleObjectsReturned:
        # If multiple active payees exist, return the first one
        return Payee.objects.filter(name=name, budget=budget, deleted=False).first()


@router.post(
    "/transactions/{budget_id}",
    tags=["Transactions"],
    response={200: TransactionSchema, 409: Error},
)
def create_transaction(
    request, budget_id: str, transaction: TransactionPostPatchSchema
):
    """Create a new transaction"""
    # Ensure the budget belongs to the user
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)

    account = get_object_or_404(Account, id=transaction.account_id)
    payee = get_or_create_payee(transaction.payee, budget)
    if transaction.envelope_id:
        envelope = get_object_or_404(Envelope, id=transaction.envelope_id)
    else:
        envelope = None

    # Check if import_id already exists
    if (
        transaction.import_id
        and Transaction.objects.filter(import_id=transaction.import_id).exists()
    ):
        return 409, {"message": "Transaction with this import_id already exists"}

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
        import_id=transaction.import_id,
    )
    return TransactionSchema.from_orm(new_transaction)


# post multiple transactions
@router.post(
    "/transactions/{budget_id}/bulk",
    response={200: List[TransactionSchema], 404: Error},
    tags=["Transactions"],
)
def create_transactions(
    request, budget_id: str, transactions: List[TransactionPostPatchSchema]
):
    """Create multiple transactions"""
    # Ensure the budget belongs to the user
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)

    # Cache accounts, payees, and envelopes
    account_ids = set(t.account_id for t in transactions)
    accounts = {a.id: a for a in Account.objects.filter(id__in=account_ids)}

    payee_names = set(t.payee for t in transactions)
    payees = {
        p.name: p
        for p in Payee.objects.filter(
            name__in=payee_names, budget=budget, deleted=False
        )
    }

    envelope_ids = set(t.envelope_id for t in transactions if t.envelope_id)
    envelopes = {e.id: e for e in Envelope.objects.filter(id__in=envelope_ids)}

    new_transactions = []
    duplicate_import_ids = []
    for transaction in transactions:
        account = accounts.get(transaction.account_id)
        if not account:
            return 404, {
                "message": f"Account with id {transaction.account_id} not found",
            }

        payee = payees.get(transaction.payee)
        if not payee:
            payee = get_or_create_payee(transaction.payee, budget)
            payees[transaction.payee] = payee

        envelope = None
        if transaction.envelope_id:
            envelope = envelopes.get(transaction.envelope_id)
            if not envelope:
                return 404, {
                    "message": f"Envelope with id {transaction.envelope_id} not found"
                }

        # Check if import_id already exists
        if (
            transaction.import_id
            and Transaction.objects.filter(
                import_id=transaction.import_id, budget=budget
            ).exists()
        ):
            duplicate_import_ids.append(transaction.import_id)
            continue

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
            import_id=transaction.import_id,
        )
        new_transactions.append(new_transaction)

    response_data = {
        "transactions": [
            TransactionSchema.from_orm(transaction) for transaction in new_transactions
        ],
        "duplicate_import_ids": duplicate_import_ids,
    }
    return response_data


@router.put(
    "/transactions/{budget_id}/{transaction_id}",
    response=TransactionSchema,
    tags=["Transactions"],
)
def update_transaction(
    request,
    budget_id: str,
    transaction_id: str,
    transaction_data: TransactionPostPatchSchema,
):
    """
    Update a transaction with the given `transaction_id` and `budget_id`, ensuring it
    belongs to the user.
    """
    # Ensure the transaction belongs to the authenticated user
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    trans = get_object_or_404(
        Transaction, id=transaction_id, budget_id=budget_id, budget__user=request.user
    )

    # Update transaction fields
    trans.account = get_object_or_404(Account, id=transaction_data.account_id)
    trans.payee = get_or_create_payee(transaction_data.payee, budget)
    if transaction_data.envelope_id is not None:
        trans.envelope = get_object_or_404(Envelope, id=transaction_data.envelope_id)
    else:
        trans.envelope = None
    trans.date = transaction_data.date
    trans.amount = transaction_data.amount
    trans.memo = transaction_data.memo
    trans.cleared = transaction_data.cleared
    trans.reconciled = transaction_data.reconciled
    trans.save()

    return TransactionSchema.from_orm(trans)


@router.patch(
    "/transactions/{budget_id}/{transaction_id}",
    response=TransactionSchema,
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


@router.delete("/transactions/{budget_id}/{transaction_id}", tags=["Transactions"])
def delete_transaction(request, budget_id: str, transaction_id: str):
    """
    Delete a transaction.
    """
    # Ensure the transaction belongs to the authenticated user
    transaction = get_object_or_404(
        Transaction, id=transaction_id, budget_id=budget_id, budget__user=request.user
    )

    # Mark the transaction as deleted
    transaction.soft_delete()
    return {"detail": "Transaction deleted successfully"}


@router.post(
    "/transactions/{budget_id}/{account_id}/import/ofx/file", tags=["Transactions"]
)
def import_ofx_file(
    request, budget_id: str, account_id: str, ofx_file: UploadedFile = File(...)
):
    """Import transactions from an OFX file"""
    # ensure the account belongs to the user
    account = get_object_or_404(Account, id=account_id, budget__user=request.user)

    # Read the OFX file content
    ofx_data = ofx_file.file.read().decode("utf-8")

    # Call the class method to import transactions
    return Transaction.import_ofx(budget_id, account.id, ofx_data)


@router.post(
    "/transactions/{budget_id}/{account_id}/import/ofx/data", tags=["Transactions"]
)
def import_ofx_data(request, budget_id: str, account_id: str, data: OFXDataSchema):
    """Import transactions from an OFX data string"""
    # ensure the account belongs to the user
    account = get_object_or_404(Account, id=account_id, budget__user=request.user)

    # Call the class method to import transactions
    return Transaction.import_ofx(budget_id, account.id, data.ofx_data)


@router.get("/payees/{budget_id}", response=List[PayeeSchema], tags=["Payees"])
def list_payees(request, budget_id: str):
    user = request.auth
    budget = get_object_or_404(Budget, id=budget_id, user=user)
    payees = Payee.objects.filter(budget=budget, deleted=False).order_by(
        "name"
    )  # Only show non-deleted payees
    return [PayeeSchema.from_orm(payee) for payee in payees]


@router.get(
    "/payees/{budget_id}/{payee_id}",
    response=PayeeSchema,
    tags=["Payees"],
)
def get_payee(request, budget_id: str, payee_id: str):
    user = request.auth
    budget = get_object_or_404(Budget, id=budget_id, user=user)
    payee = get_object_or_404(Payee, id=payee_id, budget=budget)
    return PayeeSchema.from_orm(payee)


@router.post("/payees/{budget_id}", response=PayeeSchema, tags=["Payees"])
def create_payee(request, budget_id: str, payee_in: PayeeCreateSchema):
    user = request.auth
    budget = get_object_or_404(Budget, id=budget_id, user=user)
    payee = Payee.objects.create(budget=budget, **payee_in.dict())
    return PayeeSchema.from_orm(payee)


@router.put(
    "/payees/{budget_id}/{payee_id}",
    response=PayeeSchema,
    tags=["Payees"],
)
def update_payee(request, budget_id: str, payee_id: str, payee_in: PayeeUpdateSchema):
    user = request.auth
    budget = get_object_or_404(Budget, id=budget_id, user=user)
    payee = get_object_or_404(Payee, id=payee_id, budget=budget)
    for attr, value in payee_in.dict().items():
        setattr(payee, attr, value)
    payee.save()
    return PayeeSchema.from_orm(payee)


@router.delete("/payees/{budget_id}/{payee_id}", tags=["Payees"])
def delete_payee(request, budget_id: str, payee_id: str):
    if payee_id == "delete-unused":
        return delete_unused_payees(request, budget_id)
    user = request.auth
    budget = get_object_or_404(Budget, id=budget_id, user=user)
    payee = get_object_or_404(Payee, id=payee_id, budget=budget)
    payee.deleted = True
    payee.save()
    return {"detail": "Payee deleted successfully"}


@router.delete("/payees/{budget_id}/delete-unused", tags=["Payees"])
def delete_unused_payees(request, budget_id: str):
    """
    Delete all payees that are not used in any transactions for the given budget.

    This performs a hard delete, completely removing unused payees from the database.
    """
    user = request.auth
    # Ensure the budget belongs to the authenticated user
    get_object_or_404(Budget, id=budget_id, user=user)

    # Call the method to delete unused payees
    deleted_count = Payee.delete_unused_payees(budget_id)

    return {
        "detail": f"Successfully deleted {deleted_count} unused payees",
        "count": deleted_count,
    }


@router.post(
    "/payees/{budget_id}/clean-names",
    response={200: dict, 400: Error},
    tags=["Payees"],
)
def clean_payee_names(request, budget_id: str):
    """
    Clean payee names using AI or predefined rules.
    This is a placeholder - implement your actual cleaning logic.
    """
    user = request.auth
    get_object_or_404(Budget, id=budget_id, user=user)

    try:
        # Implement your payee name cleaning logic here
        # For now, return a mock response
        cleaned_count = 0

        # Example: Get all payees and apply cleaning rules
        payees = Payee.objects.filter(budget_id=budget_id, deleted=False)

        for payee in payees:
            # Apply your cleaning logic here
            # This is just a placeholder
            original_name = payee.name
            cleaned_name = payee.name.strip().title()  # Simple example

            if original_name != cleaned_name:
                payee.name = cleaned_name
                payee.save()
                cleaned_count += 1

        return {
            "count": cleaned_count,
            "message": f"Successfully cleaned {cleaned_count} payee names",
        }
    except Exception as e:
        return 400, {"message": f"Failed to clean payee names: {str(e)}"}


def search_transactions(request, budget_id: str, query: str = ""):
    """
    Search transactions using a query language.

    Args:
        request: The request object
        budget_id: The budget ID
        query: The search query string

    Returns:
        List of transactions matching the search criteria
    """
    # Parse the query into a Django Q object
    query_filter = parse_search_query(query, budget_id)

    # Get transactions matching the filter
    transactions = Transaction.objects.filter(query_filter).order_by("-date")

    # Return the transactions
    return transactions


class PayeeMergeRequest(Schema):
    payee_ids: List[str]
    new_payee_name: str


class PayeeMergePreview(Schema):
    payee_ids: List[str]
    suggested_name: str
    payees_to_merge: List[PayeeSchema]
    transaction_count: int
    sample_transactions: List[TransactionSchema]  # First 5-10 for preview


class PayeeMergeResponse(Schema):
    merged_payee: PayeeSchema
    updated_transaction_count: int
    deleted_payee_ids: List[str]


@router.post(
    "/payees/{budget_id}/merge/preview",
    response={200: PayeeMergePreview, 400: Error},
    tags=["Payees"],
)
def preview_payee_merge(request, budget_id: str):
    """Preview what will happen when merging payees"""
    # Ensure the budget belongs to the user
    get_object_or_404(Budget, id=budget_id, user=request.user)

    # Get data from request body
    try:
        import json

        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return 400, {"message": "Invalid JSON data"}

    payee_ids = data.get("payee_ids", [])

    if len(payee_ids) < 2:
        return 400, {"message": "At least 2 payees are required for merging"}

    try:
        # Get the payees to merge
        payees = list(
            Payee.objects.filter(id__in=payee_ids, budget_id=budget_id, deleted=False)
        )

        if len(payees) != len(payee_ids):
            return 400, {"message": "One or more payees not found"}

        # Get all transactions that will be affected
        transactions = Transaction.objects.filter(
            payee__in=payees, budget_id=budget_id, deleted=False
        ).order_by("-date")

        transaction_count = transactions.count()

        # Get sample transactions (first 10 for preview)
        sample_transactions = transactions[:10]

        # Suggest a name - use the payee with the most transactions,
        # or first alphabetically if tied
        payee_transaction_counts = []
        for payee in payees:
            count = Transaction.objects.filter(
                payee=payee, budget_id=budget_id, deleted=False
            ).count()
            payee_transaction_counts.append((payee, count))
        # Sort by transaction count (desc) then by name (asc)
        payee_transaction_counts.sort(key=lambda x: (-x[1], x[0].name.lower()))
        suggested_name = payee_transaction_counts[0][0].name

        return {
            "payee_ids": payee_ids,
            "suggested_name": suggested_name,
            "payees_to_merge": [PayeeSchema.from_orm(p) for p in payees],
            "transaction_count": transaction_count,
            "sample_transactions": [
                TransactionSchema.from_orm(t) for t in sample_transactions
            ],
        }

    except Exception as e:
        logger.error("Error previewing payee merge: %s", str(e))
        return 400, {"message": f"Failed to preview merge: {str(e)}"}


@router.post(
    "/payees/{budget_id}/merge/confirm",
    response={200: PayeeMergeResponse, 400: Error},
    tags=["Payees"],
)
def confirm_payee_merge(request, budget_id: str, merge_data: PayeeMergeRequest):
    """Actually perform the payee merge"""
    # Ensure the budget belongs to the user
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)

    if len(merge_data.payee_ids) < 2:
        return 400, {"message": "At least 2 payees are required for merging"}

    if not merge_data.new_payee_name.strip():
        return 400, {"message": "New payee name cannot be empty"}

    try:
        with transaction.atomic():
            # Get the payees to merge
            payees_to_merge = list(
                Payee.objects.filter(
                    id__in=merge_data.payee_ids, budget_id=budget_id, deleted=False
                )
            )

            if len(payees_to_merge) != len(merge_data.payee_ids):
                return 400, {"message": "One or more payees not found"}

            new_name = merge_data.new_payee_name.strip()

            # Check if a payee with the new name already exists
            existing_payee = Payee.objects.filter(
                name=new_name, budget=budget, deleted=False
            ).first()

            if existing_payee and existing_payee.id not in merge_data.payee_ids:
                # If the target name exists and it's NOT one of the payees being merged
                return 400, {
                    "message": f"A payee named '{new_name}' already exists. Please choose a different name."
                }

            # Determine the target payee
            if existing_payee and existing_payee.id in merge_data.payee_ids:
                # Use the existing payee as target (it's one of the ones being merged)
                target_payee = existing_payee
                payees_to_delete = [
                    p for p in payees_to_merge if p.id != target_payee.id
                ]
            else:
                # Use the first payee as target and rename it
                target_payee = payees_to_merge[0]
                target_payee.name = new_name
                target_payee.save()
                payees_to_delete = payees_to_merge[1:]

            # Get all transactions from payees that will be deleted
            transactions_to_update = Transaction.objects.filter(
                payee__in=payees_to_delete, budget_id=budget_id, deleted=False
            )

            # Update transactions to point to the target payee
            updated_count = transactions_to_update.update(payee=target_payee)

            # Soft delete the old payees
            deleted_payee_ids = []
            for payee in payees_to_delete:
                payee.deleted = True
                payee.save()
                deleted_payee_ids.append(str(payee.id))

            logger.info(
                "Merged %d payees into '%s', updated %d transactions",
                len(merge_data.payee_ids),
                target_payee.name,
                updated_count,
            )

            return {
                "merged_payee": PayeeSchema.from_orm(target_payee),
                "updated_transaction_count": updated_count,
                "deleted_payee_ids": deleted_payee_ids,
            }

    except Exception as e:
        logger.error("Error merging payees: %s", str(e))
        return 400, {"message": f"Failed to merge payees: {str(e)}"}
