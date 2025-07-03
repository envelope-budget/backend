import logging
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from django.shortcuts import render
from django.views.generic import TemplateView

from budgets.models import Budget
from transactions.models import Transaction
from accounts.models import Account

from .utils import (
    export_budget_csv,
    export_budget_markdown,
    export_budget_xlsx,
    export_spending_by_category_csv,
    export_spending_by_category_markdown,
    export_spending_by_category_xlsx,
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
            {
                "name": "Spending by Category",
                "description": "View spending by envelope with monthly breakdown and budget comparison",
                "url_name": "reports:spending-by-category-report",
            },
            {
                "name": "Account Audit",
                "description": "Compare account balances with calculated transaction totals to identify discrepancies",
                "url_name": "reports:account-audit-report",
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
                    "current_balance": envelope.balance / 1000,
                    "monthly_budget_amount": envelope.monthly_budget_amount / 1000,
                    "note": envelope.note or "",
                }
            )

    return budget_data


@login_required
def spending_by_category_report(request):
    """
    Display spending by category report with monthly breakdown and budget comparison.
    """
    # Get the current budget using the same logic as other reports
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

    if not current_budget:
        return render(
            request,
            "reports/spending_by_category_report.html",
            {
                "current_budget": None,
            },
        )

    # Get the earliest and most recent transaction dates for this budget to determine year range
    transactions_queryset = Transaction.objects.filter(
        budget=current_budget, deleted=False
    )

    earliest_transaction = transactions_queryset.order_by("date").first()
    latest_transaction = transactions_queryset.order_by("-date").first()

    # Determine the year range for dropdown
    current_year = datetime.now().year

    if earliest_transaction and latest_transaction:
        earliest_year = earliest_transaction.date.year
        latest_year = latest_transaction.date.year
        # Extend range slightly beyond actual data
        min_year = max(earliest_year, 2015)  # Don't go before 2015
        max_year = max(latest_year, current_year) + 1  # At least current year + 1
    else:
        # If no transactions, default to reasonable range
        min_year = current_year - 3
        max_year = current_year + 1

    # Get date range from request or default to 3 months ago to current month
    today = datetime.now().date()
    current_month_start = today.replace(day=1)
    three_months_ago = current_month_start - timedelta(days=90)
    three_months_ago_start = three_months_ago.replace(day=1)

    start_month = request.GET.get("start_month", str(three_months_ago_start.month))
    start_year = request.GET.get("start_year", str(three_months_ago_start.year))
    end_month = request.GET.get("end_month", str(current_month_start.month))
    end_year = request.GET.get("end_year", str(current_month_start.year))

    try:
        start_date = datetime(int(start_year), int(start_month), 1).date()
        # Get last day of end month
        if int(end_month) == 12:
            end_date = datetime(int(end_year) + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(
                int(end_year), int(end_month) + 1, 1
            ).date() - timedelta(days=1)
    except (ValueError, TypeError):
        start_date = three_months_ago_start
        end_date = current_month_start

    # Handle export requests
    export_format = request.GET.get("export")
    if export_format in ["csv", "xlsx", "markdown"]:
        try:
            spending_data = get_spending_by_category_data_for_export(
                current_budget, start_date, end_date
            )

            if export_format == "csv":
                return export_spending_by_category_csv(
                    spending_data, current_budget.name, start_date, end_date
                )
            elif export_format == "xlsx":
                return export_spending_by_category_xlsx(
                    spending_data, current_budget.name, start_date, end_date
                )
            elif export_format == "markdown":
                return export_spending_by_category_markdown(
                    spending_data, current_budget.name, start_date, end_date
                )
        except ImportError as e:
            context = {
                "error": str(e),
                "current_budget": current_budget,
                "start_month": int(start_month),
                "start_year": int(start_year),
                "end_month": int(end_month),
                "end_year": int(end_year),
            }
            return render(request, "reports/spending_by_category_report.html", context)

    context = {
        "current_budget": current_budget,
        "start_month": int(start_month),
        "start_year": int(start_year),
        "end_month": int(end_month),
        "end_year": int(end_year),
        "start_date": start_date,
        "end_date": end_date,
        "year_choices": range(
            min_year, max_year + 1
        ),  # Dynamic range based on transaction data
        "month_choices": [  # Added month choices for cleaner template
            (1, "January"),
            (2, "February"),
            (3, "March"),
            (4, "April"),
            (5, "May"),
            (6, "June"),
            (7, "July"),
            (8, "August"),
            (9, "September"),
            (10, "October"),
            (11, "November"),
            (12, "December"),
        ],
    }

    return render(request, "reports/spending_by_category_report.html", context)


def get_spending_by_category_data_for_export(budget, start_date, end_date):
    """Helper function to get spending by category data for export"""
    from envelopes.models import Category, Envelope
    from django.db.models import Sum
    from collections import defaultdict
    from datetime import datetime

    # Calculate number of months for average
    months_diff = (
        (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    )

    # Generate list of months in the range
    months_list = []
    current_date = start_date.replace(day=1)
    while current_date <= end_date:
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

    # Get all transactions in date range
    transactions = Transaction.objects.filter(
        budget=budget,
        date__gte=start_date,
        date__lte=end_date,
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

    # Get all categories and envelopes
    categories = Category.objects.filter(budget=budget).order_by("sort_order", "name")

    export_data = []

    for category in categories:
        envelopes = Envelope.objects.filter(
            category=category, budget=budget, deleted=False
        ).order_by("sort_order", "name")

        for envelope in envelopes:
            total_spent = envelope_spending.get(envelope.id, 0) / 1000
            average_spent = total_spent / months_diff if months_diff > 0 else 0
            budget_amount = envelope.monthly_budget_amount / 1000

            # Add monthly spending data
            monthly_data = {}
            for month in months_list:
                month_key = f"{month['year']}-{month['month']:02d}"
                monthly_spending = (
                    envelope_monthly_spending[envelope.id].get(month_key, 0) / 1000
                )
                monthly_data[month["name"]] = monthly_spending

            export_data.append(
                {
                    "category_name": category.name,
                    "envelope_name": envelope.name,
                    "total_spent": total_spent,
                    "average_spent": average_spent,
                    "budget_amount": budget_amount,
                    "note": envelope.note or "",
                    "monthly_spending": monthly_data,
                    "months_list": months_list,  # Include for export functions
                }
            )

    # Add unassigned if there's spending
    if unassigned_spending > 0:
        monthly_data = {}
        for month in months_list:
            month_key = f"{month['year']}-{month['month']:02d}"
            monthly_spending = unassigned_monthly_spending.get(month_key, 0) / 1000
            monthly_data[month["name"]] = monthly_spending

        export_data.append(
            {
                "category_name": "Unassigned",
                "envelope_name": "Unassigned Transactions",
                "total_spent": unassigned_spending / 1000,
                "average_spent": (
                    (unassigned_spending / 1000) / months_diff if months_diff > 0 else 0
                ),
                "budget_amount": 0,
                "note": "Transactions not assigned to any envelope",
                "monthly_spending": monthly_data,
                "months_list": months_list,
            }
        )

    return export_data


@login_required
def account_audit_report(request):
    """
    Display account audit report comparing stored balances with calculated transaction totals.
    """
    # Get the current budget using the same logic as other reports
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

    if not current_budget:
        return render(
            request,
            "reports/account_audit_report.html",
            {
                "current_budget": None,
            },
        )

    # Get all accounts for the current budget
    accounts = Account.objects.filter(budget=current_budget, deleted=False).order_by("name")

    # Calculate transaction totals for each account
    audit_data = []
    for account in accounts:
        # Get all transactions for this account
        transactions = Transaction.objects.filter(
            account=account,
            deleted=False,
        )
        
        # Calculate total from transactions
        transaction_total = sum(t.amount for t in transactions)
        
        # Calculate cleared transactions total
        cleared_transactions = transactions.filter(cleared=True)
        cleared_total = sum(t.amount for t in cleared_transactions)
        
        # Calculate discrepancies
        balance_discrepancy = account.balance - transaction_total
        cleared_discrepancy = account.cleared_balance - cleared_total
        
        # Convert to dollars for display
        audit_data.append({
            'account': account,
            'stored_balance': account.balance / 1000,
            'calculated_balance': transaction_total / 1000,
            'balance_discrepancy': balance_discrepancy / 1000,
            'stored_cleared_balance': account.cleared_balance / 1000,
            'calculated_cleared_balance': cleared_total / 1000,
            'cleared_discrepancy': cleared_discrepancy / 1000,
            'transaction_count': transactions.count(),
            'cleared_count': cleared_transactions.count(),
            'has_discrepancy': balance_discrepancy != 0 or cleared_discrepancy != 0,
        })

    # Calculate summary statistics
    total_accounts = len(audit_data)
    accounts_with_discrepancies = sum(1 for item in audit_data if item['has_discrepancy'])
    total_balance_discrepancy = sum(item['balance_discrepancy'] for item in audit_data)
    total_cleared_discrepancy = sum(item['cleared_discrepancy'] for item in audit_data)

    context = {
        "current_budget": current_budget,
        "audit_data": audit_data,
        "summary": {
            "total_accounts": total_accounts,
            "accounts_with_discrepancies": accounts_with_discrepancies,
            "total_balance_discrepancy": total_balance_discrepancy,
            "total_cleared_discrepancy": total_cleared_discrepancy,
        },
    }

    return render(request, "reports/account_audit_report.html", context)
