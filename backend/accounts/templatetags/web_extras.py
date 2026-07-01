from django.template import Library

register = Library()


@register.filter
def get_item(d, key):
    return d.get(key, [])
