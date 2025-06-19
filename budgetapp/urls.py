"""
URL configuration for budgetapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.views.static import serve
from django.http import FileResponse
import os

from .api import api


def manifest_view(request):
    manifest_path = os.path.join(settings.BASE_DIR, "static", "manifest.json")
    return FileResponse(open(manifest_path, "rb"), content_type="application/json")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("", include("allauth.urls")),
    path("", include("budgets.urls")),
    path("accounts/", include("accounts.urls")),
    path("developer/", include("developer.urls")),
    path("envelopes/", include("envelopes.urls")),
    path("transactions/", include("transactions.urls")),
    path("reports/", include("reports.urls")),
    path("manifest.json", manifest_view, name="manifest"),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "img/favicon/favicon.ico"),
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
