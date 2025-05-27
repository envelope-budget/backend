from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def milliunit_to_currency(value):
    """Convert milliunits (amount * 1000) back to currency format"""
    if value is None:
        return "0.00"

    # Convert from milliunits back to dollars
    amount = Decimal(value) / 1000
    return f"{amount:.2f}"
