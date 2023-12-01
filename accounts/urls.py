from django.urls import path
from . import views

urlpatterns = [
    path("", views.account, name="account"),
    path("x-add-account-form", views.x_add_account_form, name="x_add_account_form"),
]
