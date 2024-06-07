from typing import List, Optional
from datetime import datetime

from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404

from .models import Envelope, Category, EnvelopeGoal

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


@router.get(
    "/{budget_id}/{envelope_id}",
    response=EnvelopeSchema,
    auth=django_auth,
    tags=["Envelopes"],
)
def get_envelope(request, budget_id: str, envelope_id: str):
    pass


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
def update_envelope(request, budget_id: str, envelope_id: str):
    pass


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
