from django.urls import path
from . import views

urlpatterns = [
    path("", views.envelopes, name="envelopes"),
]
