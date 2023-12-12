from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "set-active-budget/<str:budget_id>",
        views.set_active_budget,
        name="set_active_budget",
    ),
    path("create-budget", views.create_budget, name="create_budget"),
]
