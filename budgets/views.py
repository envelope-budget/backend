from django.shortcuts import render

from budgets.models import Budget


def home(request):
    return render(request, "budgets/home.html", {"budgets": Budget.objects.all()})
