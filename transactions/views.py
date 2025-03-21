from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from envelopes.models import Category, Envelope
from .models import Payee


@login_required
def transactions(request):
    categories = Category.objects.filter(budget=request.session.get("budget"))
    _envelopes = Envelope.objects.filter(category__in=categories).select_related(
        "category"
    )
    categorized_envelopes = []
    for category in categories:
        categorized_envelopes.append(
            {
                "category": category,
                "envelopes": [e for e in _envelopes if e.category_id == category.id],
            }
        )

    response = render(
        request,
        "transactions/transactions.html",
        {"categorized_envelopes": categorized_envelopes},
    )
    response.set_cookie("budget_id", request.session.get("budget"))
    response.delete_cookie("account_id")
    return response


@login_required
def payees(request):
    _payees = Payee.objects.filter(budget=request.session.get("budget"))
    return render(request, "transactions/payees.html", {"payees": _payees})
