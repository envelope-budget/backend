from typing import List, Optional


from ninja import Router, Schema
from ninja.security import django_auth
from django.shortcuts import get_object_or_404

from .models import Category, Envelope

router = Router()


class CreateCategorySchema(Schema):
    """
    Schema for creating a new category.

    Attributes:
        name (str): The name of the category.
        sort_order (Optional[int]): The sort order of the category. Defaults to 99.
    """

    name: str
    sort_order: Optional[int] = 99


class UpdateCategorySchema(Schema):
    """
    Schema for updating a category.

    Attributes:
        name (str): The new name of the category.
        sort_order (Optional[int]): The new sort order for the category.
        hidden (Optional[bool]): Whether the category should be hidden or not.
    """

    name: str
    sort_order: Optional[int]
    hidden: Optional[bool]


class CategorySchema(Schema):
    """
    Schema for representing a category.

    Attributes:
        id (str): The unique identifier for the category.
        name (str): The name of the category.
        balance (int): The current balance of the category.
        sort_order (int): The order in which the category should be sorted.
        hidden (bool): Whether the category is hidden or not.
        deleted (bool): Whether the category is deleted or not.
    """

    id: str
    name: str
    balance: int
    sort_order: int
    hidden: bool
    deleted: bool


@router.get(
    "/{budget_id}",
    response=List[CategorySchema],  # Specify the response type
    auth=django_auth,
    tags=["Categories"],
)
def list_categories(request, budget_id: str):
    """
    List all categories for a given budget.

    Args:
        request: The request object.
        budget_id (str): The ID of the budget.

    Returns:
        QuerySet: A queryset of categorized envelopes for the given budget.
    """
    from budgets.models import Budget

    budget = get_object_or_404(Budget, id=budget_id)
    return budget.categorized_envelopes()


@router.get(
    "/{budget_id}/{category_id}",
    response=CategorySchema,
    auth=django_auth,
    tags=["Categories"],
)
def get_categories(request, budget_id: str, category_id: str):
    """
    Get a specific category for a given budget.

    Args:
        request: The incoming request object.
        budget_id (str): The ID of the budget to get the category for.
        category_id (str): The ID of the category to retrieve.

    Returns:
        CategorySchema: The requested category.
    """
    from budgets.models import Budget

    get_object_or_404(Budget, id=budget_id)
    category = get_object_or_404(Category, id=category_id)
    return category


@router.post(
    "/{budget_id}", response=CategorySchema, auth=django_auth, tags=["Categories"]
)
def create_category(request, budget_id: str, category: CreateCategorySchema):
    """
    Create a new category for a given budget.

    Args:
        request: The incoming request object.
        budget_id (str): The ID of the budget to create the category for.
        category (CreateCategorySchema): The data for the new category.

    Returns:
        CategorySchema: The newly created category.
    """
    from budgets.models import Budget

    budget = get_object_or_404(Budget, id=budget_id)
    category = Category.objects.create(
        budget=budget,
        name=category.name,
        sort_order=category.sort_order,
    )
    return category


@router.patch(
    "/{budget_id}/{category_id}",
    response=CategorySchema,
    auth=django_auth,
    tags=["Categories"],
)
def update_category(
    request, budget_id: str, category_id: str, category: UpdateCategorySchema
):
    """
    Update an existing category for a given budget.

    Args:
        request: The incoming request object.
        budget_id (str): The ID of the budget to update the category for.
        category_id (str): The ID of the category to update.
        category (UpdateCategorySchema): The updated data for the category.

    Returns:
        CategorySchema: The updated category.
    """
    from budgets.models import Budget

    get_object_or_404(Budget, id=budget_id)
    category_obj = get_object_or_404(Category, id=category_id)
    category_obj.name = category.name or category_obj.name
    category_obj.sort_order = category.sort_order or category_obj.sort_order
    category_obj.hidden = category.hidden or category_obj.hidden
    category_obj.save(update_fields=["name", "sort_order", "hidden"])
    return category_obj


@router.delete(
    "/{budget_id}/{category_id}",
    response=CategorySchema,
    auth=django_auth,
    tags=["Categories"],
)
def delete_category(request, budget_id: str, category_id: str):
    """
    Delete a category for a given budget.

    Args:
        request: The incoming request object.
        budget_id (str): The ID of the budget to delete the category for.
        category_id (str): The ID of the category to delete.

    Returns:
        CategorySchema: The deleted category.
    """
    from budgets.models import Budget

    get_object_or_404(Budget, id=budget_id)
    category = get_object_or_404(Category, id=category_id)
    if Envelope.objects.filter(category=category, deleted=False).exists():
        raise ValueError("Cannot delete category with assigned envelopes")
    category.deleted = True
    category.save(update_fields=["deleted"])
    return category
