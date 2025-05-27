from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportListView.as_view(), name="report-list"),
    path("spending/", views.spending_report, name="spending-report"),
]
