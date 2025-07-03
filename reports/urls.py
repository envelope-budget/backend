from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportListView.as_view(), name="report-list"),
    path("spending/", views.spending_report, name="spending-report"),
    path("budget/", views.budget_report, name="budget-report"),
    path(
        "spending-by-category/",
        views.spending_by_category_report,
        name="spending-by-category-report",
    ),
    path(
        "account-audit/",
        views.account_audit_report,
        name="account-audit-report",
    ),
]
