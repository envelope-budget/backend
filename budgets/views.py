from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from budgets.models import Budget


@login_required
def home(request):
    return render(request, "budgets/home.html", {"budgets": Budget.objects.all()})
