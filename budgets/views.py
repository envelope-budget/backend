from django.core.cache import cache

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from budgets.models import Budget
from budgetapp.models import UserProfile


@login_required
def home(request):
    return redirect("transactions")


@login_required
def set_active_budget(request, budget_id):
    budget = Budget.objects.get(id=budget_id)
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    user_profile.active_budget = budget
    user_profile.save()
    request.session["budget"] = str(budget.id)
    return redirect("home")


@login_required
def create_budget(request):
    budget = Budget.objects.create(user=request.user, name=request.POST.get("name"))

    request.session["budget"] = str(budget.id)
    return redirect("home")
