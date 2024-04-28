from django.urls import path
from . import views

urlpatterns = [
    path("", views.account, name="account"),
    path(
        "exchange-plaid-token", views.exchange_plaid_token, name="exchange_plaid_token"
    ),
    path("x-add-plaid", views.x_add_plaid, name="x_add_plaid"),
    path("x-add-account-form", views.x_add_account_form, name="x_add_account_form"),
]
