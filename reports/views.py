import json
import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from django.shortcuts import render
from django.views.generic import TemplateView

from budgets.models import Budget
from transactions.models import Transaction

from .utils import (
    export_budget_csv,
    export_budget_markdown,
    export_budget_xlsx,
    export_transactions_csv,
    export_transactions_markdown,
    export_transactions_xlsx,
)

logger = logging.getLogger(__name__)


class ReportListView(LoginRequiredMixin, TemplateView):
    template_name = "reports/report_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reports"] = [
            {
                "name": "Spending Report",
                "description": "View all transactions between selected dates",
                "url_name": "reports:spending-report",
            },
            {
                "name": "Budget Report",
                "description": "View monthly budget allocations for all envelopes",
                "url_name": "reports:budget-report",
            },
        ]
        return context


@login_required
def spending_report(request):
    """
    Display spending report with optional export functionality.
    """
    # Get the current budget using the same logic as context_processors.py
    current_budget = None
    user_budgets = Budget.objects.filter(user=request.user)
    active_budget_id = request.session.get("budget")

    if (
        not active_budget_id
        and hasattr(request.user, "profile")
        and request.user.profile.active_budget
    ):
        active_budget_id = request.user.profile.active_budget.id
        request.session["budget"] = active_budget_id

    for b in user_budgets:
        if str(b.id) == str(active_budget_id):
            current_budget = b
            break

    if not current_budget:
        budget_count = len(user_budgets)
        if budget_count == 0:
            current_budget = Budget.objects.create(user=request.user, name="My Budget")
        elif budget_count == 1:
            current_budget = user_budgets.first()
        else:
            # use the last opened budget
            current_budget = (
                Budget.objects.filter(user=request.user).order_by("-created_at").first()
            )
        request.session["budget"] = current_budget.id

    if not current_budget:
        return render(
            request,
            "reports/spending_report.html",
            {
                "current_budget": None,
            },
        )

    # Get date range from request or default to current month
    today = datetime.now().date()
    start_of_month = today.replace(day=1)

    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = start_of_month

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = today

    # Get transactions for the date range
    transactions = (
        Transaction.objects.filter(
            budget=current_budget,
            date__gte=start_date,
            date__lte=end_date,
            deleted=False,
        )
        .select_related("payee", "account", "envelope")
        .order_by("-date", "-id")
    )

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format in ["csv", "xlsx", "markdown"]:
        try:
            if export_format == "csv":
                return export_transactions_csv(
                    transactions,
                    start_date,
                    end_date,
                )
            elif export_format == "xlsx":
                return export_transactions_xlsx(
                    transactions, start_date, end_date, current_budget.name
                )
            elif export_format == "markdown":
                return export_transactions_markdown(
                    transactions, start_date, end_date, current_budget.name
                )
        except ImportError as e:
            # Handle missing dependencies gracefully
            context = {
                "error": str(e),
                "current_budget": current_budget,
                "transactions": transactions,
                "start_date": start_date,
                "end_date": end_date,
            }
            return render(request, "reports/spending_report.html", context)

    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.amount > 0) / 1000
    total_spent = abs(sum(t.amount for t in transactions if t.amount < 0)) / 1000
    net_amount = (sum(t.amount for t in transactions)) / 1000

    context = {
        "current_budget": current_budget,
        "transactions": transactions,
        "start_date": start_date,
        "end_date": end_date,
        "total_income": total_income,
        "total_spent": total_spent,
        "net_amount": net_amount,
    }

    return render(request, "reports/spending_report.html", context)


@login_required
def budget_report(request):
    """
    Display budget report with editable monthly allocations.
    """
    # Get the current budget using the same logic as context_processors.py
    current_budget = None
    user_budgets = Budget.objects.filter(user=request.user)
    active_budget_id = request.session.get("budget")

    if (
        not active_budget_id
        and hasattr(request.user, "profile")
        and request.user.profile.active_budget
    ):
        active_budget_id = request.user.profile.active_budget.id
        request.session["budget"] = active_budget_id

    for b in user_budgets:
        if str(b.id) == str(active_budget_id):
            current_budget = b
            break

    if not current_budget:
        budget_count = len(user_budgets)
        if budget_count == 0:
            current_budget = Budget.objects.create(user=request.user, name="My Budget")
        elif budget_count == 1:
            current_budget = user_budgets.first()
        else:
            current_budget = (
                Budget.objects.filter(user=request.user).order_by("-created_at").first()
            )
        request.session["budget"] = current_budget.id

    # Handle export requests
    export_format = request.GET.get("export")
    if export_format in ["csv", "xlsx", "markdown"] and current_budget:
        try:
            # Get the budget data for export
            budget_data = get_budget_data_for_export(current_budget)

            if export_format == "csv":
                return export_budget_csv(budget_data, current_budget.name)
            elif export_format == "xlsx":
                return export_budget_xlsx(budget_data, current_budget.name)
            elif export_format == "markdown":
                return export_budget_markdown(budget_data, current_budget.name)
        except ImportError as e:
            # Handle missing dependencies gracefully
            context = {
                "error": str(e),
                "current_budget": current_budget,
            }
            return render(request, "reports/budget_report.html", context)

    context = {
        "current_budget": current_budget,
    }

    return render(request, "reports/budget_report.html", context)


def get_budget_data_for_export(budget):
    """Helper function to get budget data in the format needed for export"""
    from envelopes.models import Category, Envelope

    categories = Category.objects.filter(budget=budget).order_by("sort_order", "name")

    budget_data = []

    for category in categories:
        envelopes = Envelope.objects.filter(
            category=category, budget=budget, deleted=False
        ).order_by("sort_order", "name")

        for envelope in envelopes:
            budget_data.append(
                {
                    "category_name": category.name,
                    "envelope_name": envelope.name,
                    "monthly_budget_amount": envelope.monthly_budget_amount / 1000,
                    "note": envelope.note or "",
                }
            )

    return budget_data
