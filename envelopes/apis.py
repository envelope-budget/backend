from typing import List, Optional

from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404

from .models import Envelope, Category

router = Router()


class createEnvelopeSchema(Schema):
    name: str
    category_id: str
    balance: int
    note: str
    monthly_budget_amount: int = 0


class EnvelopeSchema(Schema):
    id: str
    budget_id: str
    category_id: Optional[str]
    name: str
    sort_order: int = 99
    balance: int
    monthly_budget_amount: int = 0
    hidden: bool = False
    deleted: bool = False


class CategorySchema(Schema):
    id: str
    name: str
    balance: int
    sort_order: int
    hidden: bool
    deleted: bool
    envelopes: List[EnvelopeSchema]


class UnallocatedEnvelopeSchema(Schema):
    id: str
    name: str
    balance: int


class BudgetDataSchema(Schema):
    id: str
    name: str
    unallocated_envelope: UnallocatedEnvelopeSchema


class EnvelopeGoalSchema(Schema):
    id: str
    envelope_id: str
    type: str
    day: Optional[int]
    cadence: Optional[str]
    cadence_frequency: Optional[int]
    creation_month: Optional[int]
    target_amount: Optional[int]
    target_month: Optional[int]
    percentage_completed: Optional[int]
    months_to_budget: Optional[int]
    under_funded: Optional[int]
    overall_funded: Optional[int]
    overall_left: Optional[int]


class EnvelopeOrderItem(Schema):
    id: str
    order: int


class CategoryOrderItem(Schema):
    id: str
    order: int


class EnvelopeOrderSchema(Schema):
    category_id: str
    envelopes: List[EnvelopeOrderItem]


class CategoryOrderSchema(Schema):
    categories: List[CategoryOrderItem]


class UpdateEnvelopeSchema(Schema):
    name: Optional[str] = None
    balance: Optional[int] = None
    category_id: Optional[str] = None
    note: Optional[str] = None
    sort_order: Optional[int] = None
    hidden: Optional[bool] = None
    monthly_budget_amount: Optional[int] = None


class CreateCategorySchema(Schema):
    name: str


class UpdateCategorySchema(Schema):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    hidden: Optional[bool] = None


@router.get(
    "/{budget_id}",
    response=List[CategorySchema],
    auth=django_auth,
    tags=["Envelopes"],
)
def list_envelopes(request, budget_id: str):
    from budgets.models import Budget

    budget = get_object_or_404(Budget, id=budget_id)
    return budget.categorized_envelopes()


@router.get(
    "/budgets/{budget_id}",
    response=BudgetDataSchema,
    auth=django_auth,
    tags=["Budgets"],
)
def get_budget_data(request, budget_id: str):
    from budgets.models import Budget

    budget = get_object_or_404(Budget, id=budget_id)
    unallocated = Envelope.objects.get_unallocated_funds(budget)

    return {
        "id": budget.id,
        "name": budget.name,
        "unallocated_envelope": {
            "id": unallocated.id,
            "name": unallocated.name,
            "balance": unallocated.balance,
        },
    }


@router.post(
    "/categories/{budget_id}",
    response=CategorySchema,
    auth=django_auth,
    tags=["Categories"],
)
def create_category(request, budget_id: str, data: CreateCategorySchema):
    from budgets.models import Budget

    budget = get_object_or_404(Budget, id=budget_id)
    category = Category.objects.create(
        budget=budget,
        name=data.name,
    )

    # Return the category with empty envelopes list
    return {
        "id": category.id,
        "name": category.name,
        "balance": 0,
        "sort_order": category.sort_order,
        "hidden": category.hidden,
        "deleted": category.deleted,
        "envelopes": [],
    }


@router.patch(
    "/categories/{budget_id}/{category_id}",
    response=CategorySchema,
    auth=django_auth,
    tags=["Categories"],
)
def update_category(
    request, budget_id: str, category_id: str, data: UpdateCategorySchema
):
    from budgets.models import Budget

    budget = get_object_or_404(Budget, id=budget_id)
    category = get_object_or_404(Category, id=category_id, budget=budget)

    # Update only the fields that are provided
    if data.name is not None:
        category.name = data.name
    if data.sort_order is not None:
        category.sort_order = data.sort_order
    if data.hidden is not None:
        category.hidden = data.hidden

    category.save()

    # Return the updated category with its envelopes
    envelopes = Envelope.objects.filter(category=category, deleted=False).order_by(
        "sort_order", "name"
    )

    return {
        "id": category.id,
        "name": category.name,
        "balance": sum(env.balance for env in envelopes),
        "sort_order": category.sort_order,
        "hidden": category.hidden,
        "deleted": category.deleted,
        "envelopes": [
            {
                "id": env.id,
                "budget_id": env.budget_id,
                "category_id": env.category_id,
                "name": env.name,
                "sort_order": env.sort_order,
                "balance": env.balance,
                "hidden": env.hidden,
                "deleted": env.deleted,
            }
            for env in envelopes
        ],
    }


@router.delete(
    "/categories/{budget_id}/{category_id}",
    response=dict,
    auth=django_auth,
    tags=["Categories"],
)
def delete_category(request, budget_id: str, category_id: str):
    from budgets.models import Budget

    budget = get_object_or_404(Budget, id=budget_id)
    category = get_object_or_404(Category, id=category_id, budget=budget)

    # Soft delete the category
    category.deleted = True
    category.save()

    # Also soft delete all envelopes in this category
    Envelope.objects.filter(category=category).update(deleted=True)

    return {"success": True, "message": "Category deleted successfully"}


@router.post(
    "/{budget_id}/order",
    response=dict,
    auth=django_auth,
    tags=["Envelopes"],
)
def set_envelopes_order(request, budget_id: str, data: EnvelopeOrderSchema):
    """Set the order of envelopes within a category"""
    from budgets.models import Budget

    # Verify the budget exists
    get_object_or_404(Budget, id=budget_id)

    # Verify the category exists
    get_object_or_404(Category, id=data.category_id, budget_id=budget_id)

    # Update the sort order for each envelope
    for item in data.envelopes:
        envelope = get_object_or_404(
            Envelope, id=item.id, budget_id=budget_id, category_id=data.category_id
        )
        envelope.sort_order = item.order
        envelope.save()

    return {"success": True, "message": "Envelope order updated successfully"}


@router.post(
    "/categories/{budget_id}/order",
    response=dict,
    auth=django_auth,
    tags=["Categories"],
)
def set_categories_order(request, budget_id: str, data: CategoryOrderSchema):
    """Set the order of categories"""
    from budgets.models import Budget

    # Verify the budget exists
    get_object_or_404(Budget, id=budget_id)

    # Update the sort order for each category
    for item in data.categories:
        category = get_object_or_404(Category, id=item.id, budget_id=budget_id)
        category.sort_order = item.order
        category.save()

    return {"success": True, "message": "Category order updated successfully"}


class EnvelopeTransferSchema(Schema):
    from_envelope_id: str
    to_envelope_id: str
    amount: int


@router.post(
    "/{budget_id}/transfer",
    response=dict,
    auth=django_auth,
    tags=["Envelopes"],
)
def transfer_funds(request, budget_id: str, data: EnvelopeTransferSchema):
    """
    Transfer funds between envelopes.

    Args:
        budget_id: The budget ID
        data: Transfer details including source envelope, destination envelope, and amount

    Returns:
        A dictionary with the transfer result
    """
    from budgets.models import Budget

    # Verify the budget exists
    budget = get_object_or_404(Budget, id=budget_id)

    # Handle special case for unallocated funds
    if data.from_envelope_id == "unallocated":
        source_envelope = Envelope.objects.get_unallocated_funds(budget)
    else:
        source_envelope = get_object_or_404(
            Envelope, id=data.from_envelope_id, budget_id=budget_id
        )

    if data.to_envelope_id == "unallocated":
        destination_envelope = Envelope.objects.get_unallocated_funds(budget)
    else:
        destination_envelope = get_object_or_404(
            Envelope, id=data.to_envelope_id, budget_id=budget_id
        )

    # Perform the transfer
    try:
        # Use the existing transfer method from the Envelope model
        Envelope.transfer(data.amount, source_envelope, destination_envelope)

        # Get the affected categories to return updated balances
        affected_categories = []

        # Add source envelope's category if it has one and isn't unallocated
        if hasattr(source_envelope, "category") and source_envelope.category:
            source_category = source_envelope.category
            source_category_balance = sum(
                env.balance
                for env in Envelope.objects.filter(
                    category=source_category, deleted=False
                )
            )
            source_category.balance -= data.amount
            source_category.save()
            affected_categories.append(
                {
                    "id": source_category.id,
                    "name": source_category.name,
                    "balance": source_category_balance,
                }
            )

        # Add destination envelope's category if it has one, isn't unallocated,
        # and is different from source category
        if (
            hasattr(destination_envelope, "category")
            and destination_envelope.category
            and destination_envelope.category
            != getattr(source_envelope, "category", None)
        ):
            dest_category = destination_envelope.category
            dest_category_balance = sum(
                env.balance
                for env in Envelope.objects.filter(
                    category=dest_category, deleted=False
                )
            )
            dest_category.balance += data.amount
            dest_category.save()
            affected_categories.append(
                {
                    "id": dest_category.id,
                    "name": dest_category.name,
                    "balance": dest_category_balance,
                }
            )

        # Get the current unallocated envelope balance
        unallocated_envelope = Envelope.objects.get_unallocated_funds(budget)

        return {
            "success": True,
            "message": "Funds transferred successfully",
            "source_envelope": {
                "id": source_envelope.id,
                "name": source_envelope.name,
                "balance": source_envelope.balance,
            },
            "destination_envelope": {
                "id": destination_envelope.id,
                "name": destination_envelope.name,
                "balance": destination_envelope.balance,
            },
            "unallocated_envelope": {
                "id": unallocated_envelope.id,
                "name": unallocated_envelope.name,
                "balance": unallocated_envelope.balance,
            },
            "affected_categories": affected_categories,
            "amount": data.amount,
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get(
    "/{budget_id}/{envelope_id}",
    response=EnvelopeSchema,
    auth=django_auth,
    tags=["Envelopes"],
)
def get_envelope(request, budget_id: str, envelope_id: str):
    envelope = get_object_or_404(Envelope, id=envelope_id, budget_id=budget_id)
    return envelope


@router.post(
    "/{budget_id}", response=EnvelopeSchema, auth=django_auth, tags=["Envelopes"]
)
def create_envelope(request, budget_id: str, envelope: createEnvelopeSchema):
    from budgets.models import Budget

    budget = get_object_or_404(Budget, id=budget_id)
    envelope = Envelope.objects.create(
        budget=budget,
        name=envelope.name,
        category_id=envelope.category_id,
        balance=envelope.balance,
        note=envelope.note,
        monthly_budget_amount=envelope.monthly_budget_amount,
    )
    return envelope


@router.patch(
    "/{budget_id}/{envelope_id}",
    response=EnvelopeSchema,
    auth=django_auth,
    tags=["Envelopes"],
)
def update_envelope(
    request, budget_id: str, envelope_id: str, data: UpdateEnvelopeSchema
):
    envelope = get_object_or_404(Envelope, id=envelope_id, budget_id=budget_id)

    # Update only the fields that are provided
    if data.name is not None:
        envelope.name = data.name
    if data.balance is not None:
        envelope.balance = data.balance
    if data.category_id is not None:
        envelope.category_id = data.category_id
    if data.note is not None:
        envelope.note = data.note
    if data.sort_order is not None:
        envelope.sort_order = data.sort_order
    if data.hidden is not None:
        envelope.hidden = data.hidden
    if data.monthly_budget_amount is not None:
        envelope.monthly_budget_amount = data.monthly_budget_amount

    envelope.save()
    return envelope


class DeleteEnvelopeResponse(Schema):
    success: bool
    message: str
    has_transactions: bool
    action_taken: str  # "deleted" or "archived"


@router.delete(
    "/{budget_id}/{envelope_id}",
    response=DeleteEnvelopeResponse,
    auth=django_auth,
    tags=["Envelopes"],
)
def delete_envelope(request, budget_id: str, envelope_id: str):
    from transactions.models import Transaction

    envelope = get_object_or_404(Envelope, id=envelope_id, budget_id=budget_id)

    # Check if envelope has any transactions
    has_transactions = Transaction.objects.filter(envelope=envelope).exists()

    if has_transactions:
        # Archive the envelope instead of deleting
        envelope.deleted = True
        envelope.save()
        return {
            "success": True,
            "message": "Envelope archived successfully (had transactions)",
            "has_transactions": True,
            "action_taken": "archived",
        }
    else:
        # Actually delete the envelope
        envelope.delete()
        return {
            "success": True,
            "message": "Envelope deleted successfully",
            "has_transactions": False,
            "action_taken": "deleted",
        }
