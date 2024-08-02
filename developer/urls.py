from django.urls import path
from . import views

urlpatterns = [
    path("api-keys", views.APIKeysView.as_view(), name="api_keys"),
]
