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


class EnvelopeSchema(Schema):
    id: str
    budget_id: str
    category_id: Optional[str]
    name: str
    sort_order: int = 99
    balance: int
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


@router.get(
    "/{budget_id}",
    response=List[CategorySchema],  # Specify the response type
    auth=django_auth,
    tags=["Envelopes"],
)
def list_envelopes(request, budget_id: str):
    from budgets.models import Budget

    budget = get_object_or_404(Budget, id=budget_id)
    return budget.categorized_envelopes()


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

    envelope.save()
    return envelope


@router.delete(
    "/{budget_id}/{envelope_id}",
    response=EnvelopeSchema,
    auth=django_auth,
    tags=["Envelopes"],
)
def delete_envelope(request, budget_id: str, envelope_id: str):
    envelope = get_object_or_404(Envelope, id=envelope_id, budget_id=budget_id)
    envelope.deleted = True
    envelope.save()
    return envelope
