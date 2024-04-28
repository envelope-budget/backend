from django.urls import path
from . import views

urlpatterns = [
    path("", views.transactions, name="transactions"),
    path("payees/", views.payees, name="payees"),
]
