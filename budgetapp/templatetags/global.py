from django import template

register = template.Library()


@register.filter(name="money")
def money(value):
    if type(value) == int:
        if value >= 0:
            return f"${value/1000:,.2f}"
        else:
            return f"-${(0-value)/1000:,.2f}"
    return "???"
