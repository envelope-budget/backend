from uuid import UUID
from typing import List

from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404
from .models import Budget

router = Router()


class BudgetSchema(Schema):
    id: UUID
    user_id: int
    name: str
    date_format: str
    currency_iso_code: str
    currency_decimal_digits: int
    currency_decimal_separator: str
    currency_symbol_first: bool
    currency_group_separator: str
    currency_symbol: str
    currency_display_symbol: bool

    @classmethod
    def from_django(cls, obj):
        return cls(
            id=obj.id,
            user_id=obj.user_id,  # Assuming you want the user's ID
            name=obj.name,
            date_format=obj.date_format,
            currency_iso_code=obj.currency_iso_code,
            currency_decimal_digits=obj.currency_decimal_digits,
            currency_decimal_separator=obj.currency_decimal_separator,
            currency_symbol_first=obj.currency_symbol_first,
            currency_group_separator=obj.currency_group_separator,
            currency_symbol=obj.currency_symbol,
            currency_display_symbol=obj.currency_display_symbol,
        )


@router.get("", response=List[BudgetSchema], auth=django_auth, tags=["Budgets"])
def list_budgets(request):
    user = request.auth
    budgets = Budget.objects.filter(user=user)
    return [BudgetSchema.from_django(budget) for budget in budgets]


@router.get("/{budget_id}", response=BudgetSchema, auth=django_auth, tags=["Budgets"])
def get_budget(request, budget_id: UUID):
    budget = get_object_or_404(Budget, id=budget_id)
    return BudgetSchema.from_django(budget)
