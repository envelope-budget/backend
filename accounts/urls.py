from django.urls import path
from . import views

urlpatterns = [
    path("", views.account, name="account"),
    path(
        "exchange-plaid-token", views.exchange_plaid_token, name="exchange_plaid_token"
    ),
    path("x-add-plaid", views.x_add_plaid, name="x_add_plaid"),
    path("x-add-sfin", views.x_add_sfin, name="x_add_sfin"),
    path("x-add-account-form", views.x_add_account_form, name="x_add_account_form"),
    path("<slug:slug>/", views.account_transactions, name="account_transactions"),
    path("edit/<str:account_id>/", views.edit_account_form, name="edit_account"),
]
