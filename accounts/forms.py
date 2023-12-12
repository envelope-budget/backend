from django import forms

from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = [
            "name",
            "type",
            "note",
            "balance",
        ]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 4}),
        }
