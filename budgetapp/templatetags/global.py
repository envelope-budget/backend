from django import template

register = template.Library()


@register.filter(name="money")
def money(value):
    return f"${value/1000:,.2f}"
