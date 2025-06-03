from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404
from typing import List, Optional
from budgets.models import Budget
from envelopes.models import Envelope, Category

router = Router()


class EnvelopeBudgetSchema(Schema):
    id: str
    name: str
    monthly_budget_amount_dollars: float
    note: Optional[str] = None


class CategoryBudgetSchema(Schema):
    category: dict
    envelopes: List[EnvelopeBudgetSchema]
    category_total: float


@router.get(
    "/budget-data/{budget_id}",
    response=List[CategoryBudgetSchema],
    auth=django_auth,
    tags=["Reports"],
)
def get_budget_report_data(request, budget_id: str):
    """
    Get budget report data for a specific budget.
    """
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)

    # Get all categories with their envelopes
    categories = Category.objects.filter(budget=budget).order_by("sort_order", "name")

    budget_data = []

    for category in categories:
        envelopes = Envelope.objects.filter(
            category=category, budget=budget, deleted=False
        ).order_by("sort_order", "name")

        envelope_data = []
        category_total = 0

        for envelope in envelopes:
            monthly_budget_dollars = envelope.monthly_budget_amount / 1000
            category_total += monthly_budget_dollars

            envelope_data.append(
                {
                    "id": envelope.id,
                    "name": envelope.name,
                    "monthly_budget_amount_dollars": monthly_budget_dollars,
                    "note": envelope.note or "",
                }
            )

        budget_data.append(
            {
                "category": {
                    "id": category.id,
                    "name": category.name,
                },
                "envelopes": envelope_data,
                "category_total": category_total,
            }
        )

    return budget_data


class BudgetChangeSchema(Schema):
    envelope_id: str
    original_value: float
    new_value: float


class BulkBudgetUpdateSchema(Schema):
    changes: List[BudgetChangeSchema]


@router.post(
    "/budget/bulk-update",
    response=dict,
    auth=django_auth,
    tags=["Reports"],
)
def bulk_update_budget_amounts(request, data: BulkBudgetUpdateSchema):
    """
    Bulk update monthly budget amounts for multiple envelopes.
    """
    try:
        updated_envelopes = []

        for change in data.changes:
            envelope = get_object_or_404(Envelope, id=change.envelope_id)

            # Verify the envelope belongs to the user's budget
            if envelope.budget.user != request.user:
                return {"success": False, "message": "Unauthorized access to envelope"}

            # Convert dollars to cents for storage
            new_amount_cents = int(change.new_value * 1000)
            envelope.monthly_budget_amount = new_amount_cents
            envelope.save()

            updated_envelopes.append(
                {
                    "id": envelope.id,
                    "name": envelope.name,
                    "monthly_budget_amount": new_amount_cents,
                }
            )

        return {
            "success": True,
            "message": f"Updated {len(updated_envelopes)} envelope(s)",
            "updated_envelopes": updated_envelopes,
        }

    except Exception as e:
        return {"success": False, "message": str(e)}
