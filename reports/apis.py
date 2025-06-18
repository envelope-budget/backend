from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404
from typing import List, Optional
from budgets.models import Budget
from envelopes.models import Envelope, Category
from datetime import timedelta
from collections import defaultdict
from django.db.models import Sum

router = Router()


class EnvelopeBudgetSchema(Schema):
    id: str
    name: str
    monthly_budget_amount_dollars: float
    balance: float
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
            balance_dollars = envelope.balance / 1000
            category_total += monthly_budget_dollars

            envelope_data.append(
                {
                    "id": envelope.id,
                    "name": envelope.name,
                    "monthly_budget_amount_dollars": monthly_budget_dollars,
                    "balance": balance_dollars,
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


@router.get(
    "/spending-by-category-data/{budget_id}",
    response=dict,
    auth=django_auth,
    tags=["Reports"],
)
def get_spending_by_category_data(
    request, budget_id: str, start_date: str, end_date: str
):
    """
    Get spending by category data for a specific budget and date range.
    """
    from transactions.models import Transaction
    from datetime import datetime
    from collections import defaultdict

    budget = get_object_or_404(Budget, id=budget_id, user=request.user)

    # Parse dates
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format"}

    # Calculate number of months for average
    months_diff = (
        (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1
    )

    # Generate list of months in the range
    months_list = []
    current_date = start_dt.replace(day=1)
    while current_date <= end_dt:
        months_list.append(
            {
                "year": current_date.year,
                "month": current_date.month,
                "name": current_date.strftime("%B %Y"),
            }
        )
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    # Get all transactions in date range (only expenses)
    transactions = Transaction.objects.filter(
        budget=budget,
        date__gte=start_dt,
        date__lte=end_dt,
        deleted=False,
        amount__lt=0,  # Only expenses
    ).select_related("envelope", "envelope__category")

    # Group spending by envelope and month
    envelope_monthly_spending = defaultdict(lambda: defaultdict(int))
    envelope_spending = defaultdict(int)
    unassigned_monthly_spending = defaultdict(int)
    unassigned_spending = 0

    for transaction in transactions:
        month_key = f"{transaction.date.year}-{transaction.date.month:02d}"
        amount = abs(transaction.amount)

        if transaction.envelope:
            envelope_monthly_spending[transaction.envelope.id][month_key] += amount
            envelope_spending[transaction.envelope.id] += amount
        else:
            unassigned_monthly_spending[month_key] += amount
            unassigned_spending += amount

    # Get all categories with their envelopes
    categories = Category.objects.filter(budget=budget).order_by("sort_order", "name")

    spending_data = []

    for category in categories:
        envelopes = Envelope.objects.filter(
            category=category, budget=budget, deleted=False
        ).order_by("sort_order", "name")

        envelope_data = []
        category_total = 0

        for envelope in envelopes:
            total_spent = envelope_spending.get(envelope.id, 0)
            total_spent_dollars = total_spent / 1000
            average_spent_dollars = (
                total_spent_dollars / months_diff if months_diff > 0 else 0
            )
            budget_amount_dollars = envelope.monthly_budget_amount / 1000

            category_total += total_spent_dollars

            # Add monthly spending data
            monthly_spending = {}
            for month in months_list:
                month_key = f"{month['year']}-{month['month']:02d}"
                monthly_amount = (
                    envelope_monthly_spending[envelope.id].get(month_key, 0) / 1000
                )
                monthly_spending[month["name"]] = monthly_amount

            envelope_data.append(
                {
                    "id": envelope.id,
                    "name": envelope.name,
                    "total_spent": total_spent_dollars,
                    "average_spent": average_spent_dollars,
                    "monthly_budget_amount_dollars": budget_amount_dollars,
                    "note": envelope.note or "",
                    "monthly_spending": monthly_spending,
                }
            )

        if envelope_data:  # Only include categories that have envelopes
            spending_data.append(
                {
                    "category": {
                        "id": category.id,
                        "name": category.name,
                    },
                    "envelopes": envelope_data,
                    "category_total": category_total,
                }
            )

    # Add unassigned transactions if any
    if unassigned_spending > 0:
        unassigned_total = unassigned_spending / 1000

        monthly_spending = {}
        for month in months_list:
            month_key = f"{month['year']}-{month['month']:02d}"
            monthly_amount = unassigned_monthly_spending.get(month_key, 0) / 1000
            monthly_spending[month["name"]] = monthly_amount

        spending_data.append(
            {
                "category": {
                    "id": "unassigned",
                    "name": "Unassigned",
                },
                "envelopes": [
                    {
                        "id": "unassigned",
                        "name": "Unassigned Transactions",
                        "total_spent": unassigned_total,
                        "average_spent": (
                            unassigned_total / months_diff if months_diff > 0 else 0
                        ),
                        "monthly_budget_amount_dollars": 0,
                        "note": "Transactions not assigned to any envelope",
                        "monthly_spending": monthly_spending,
                    }
                ],
                "category_total": unassigned_total,
            }
        )

    return {
        "spending_data": spending_data,
        "months_count": months_diff,
        "months_list": months_list,
        "date_range": {
            "start": start_date,
            "end": end_date,
        },
    }
