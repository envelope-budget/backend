from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from budgets.models import Budget


@login_required
def envelopes(request):
    return render(
        request,
        "envelopes/envelopes.html",
        {},
    )
