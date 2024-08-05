from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from budgetapp.models import APIKey


class APIKeysView(LoginRequiredMixin, TemplateView):
    template_name = "developer/api_keys.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_keys"] = APIKey.objects.filter(user=self.request.user)
        return context
