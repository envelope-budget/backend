from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Category, Envelope


@login_required
def envelopes(request):
    return render(
        request,
        "envelopes/envelopes.html",
        {},
    )


@login_required
def category_and_envelopes_json(request):
    categories = Category.objects.filter(
        budget=request.session.get("budget"), hidden=False
    )
    _envelopes = Envelope.objects.filter(category__in=categories).select_related(
        "category"
    )
    categorized_envelopes = []
    for category in categories:
        category_data = {
            "id": category.id,
            "name": category.name,
            "balance": category.balance / 1000,
            "sort_order": category.sort_order,
        }

        envelope_list = []
        for e in _envelopes:
            if e.category_id == category.id:
                envelope_list.append(
                    {
                        "id": e.id,
                        "name": e.name,
                        "balance": e.balance / 1000,
                        # Add other envelope fields as needed
                    }
                )

        categorized_envelopes.append(
            {
                "category": category_data,
                "envelopes": envelope_list,
            }
        )

    return JsonResponse({"categorized_envelopes": categorized_envelopes})
