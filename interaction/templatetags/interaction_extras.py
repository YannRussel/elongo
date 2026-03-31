from django import template

register = template.Library()


@register.filter
def get_item(data, key):
    if data:
        return data.get(key)
    return None


@register.filter
def addstr(value, arg):
    return f"{value}{arg}"