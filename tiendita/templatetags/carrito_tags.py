from django import template
import json

register = template.Library()

@register.filter
def json_parse(value):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}

@register.filter
def sum_quantities(items):
    try:
        return sum(item.get('cantidad', 0) for item in items)
    except (TypeError, AttributeError):
        return 0 