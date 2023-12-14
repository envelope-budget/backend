from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def transactions(request):
    response = render(request, "transactions/transactions.html")
    response.set_cookie("budget_id", request.session.get("budget"))
    return response
