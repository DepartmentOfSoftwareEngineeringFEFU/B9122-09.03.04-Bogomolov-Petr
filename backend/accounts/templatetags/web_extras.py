from django.template import Library

register = Library()


@register.filter
def get_item(d, key):
    return d.get(key, [])


@register.filter
def dictkey(d, key):
    return d.get(key)


@register.filter
def attr(obj, name):
    return getattr(obj, name, '')
