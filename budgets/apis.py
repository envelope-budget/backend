from uuid import UUID
from typing import List, Optional

from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404
from .models import Budget

router = Router()


class createBudgetSchema(Schema):
    name: str
    date_format: Optional[str] = "MM/DD/YYYY"
    currency_iso_code: Optional[str] = "USD"
    currency_decimal_digits: Optional[int] = 2
    currency_decimal_separator: Optional[str] = "."
    currency_symbol_first: Optional[bool] = True
    currency_group_separator: Optional[str] = ","
    currency_symbol: Optional[str] = "$"
    currency_display_symbol: Optional[bool] = True


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


@router.post("", response=BudgetSchema, auth=django_auth, tags=["Budgets"])
def create_budget(request, payload: createBudgetSchema):
    budget = Budget.objects.create(
        user=request.auth,
        name=payload.name,
        date_format=payload.date_format,
        currency_iso_code=payload.currency_iso_code,
        currency_decimal_digits=payload.currency_decimal_digits,
        currency_decimal_separator=payload.currency_decimal_separator,
        currency_symbol_first=payload.currency_symbol_first,
        currency_group_separator=payload.currency_group_separator,
        currency_symbol=payload.currency_symbol,
        currency_display_symbol=payload.currency_display_symbol,
    )
    return BudgetSchema.from_django(budget)


@router.get("", response=List[BudgetSchema], auth=django_auth, tags=["Budgets"])
def list_budgets(request):
    user = request.auth
    budgets = Budget.objects.filter(user=user)
    return [BudgetSchema.from_django(budget) for budget in budgets]


@router.get("/{budget_id}", response=BudgetSchema, auth=django_auth, tags=["Budgets"])
def get_budget(request, budget_id: UUID):
    budget = get_object_or_404(Budget, id=budget_id)
    return BudgetSchema.from_django(budget)
