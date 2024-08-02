from django.views.generic import TemplateView


class APIKeysView(TemplateView):
    template_name = "developer/api_keys.html"
