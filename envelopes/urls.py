from django.urls import path
from . import views

urlpatterns = [
    path("", views.envelopes, name="envelopes"),
    path(
        "categorized_envelopes.json",
        views.category_and_envelopes_json,
        name="categories_json",
    ),
]
