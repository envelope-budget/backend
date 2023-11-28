from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def envelopes(request):
    return render(request, "envelopes/envelopes.html")
