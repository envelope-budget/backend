from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from envelopes.models import Category, Envelope


@login_required
def transactions(request):
    categories = Category.objects.filter(budget=request.session.get("budget"))
    categorized_envelopes = []
    for category in categories:
        categorized_envelopes.append(
            {
                "category": category,
                "envelopes": Envelope.objects.filter(category=category),
            }
        )

    response = render(
        request,
        "transactions/transactions.html",
        {"categorized_envelopes": categorized_envelopes},
    )
    response.set_cookie("budget_id", request.session.get("budget"))
    return response
