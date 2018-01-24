from django import template
register = template.Library()


@register.filter
def keyvalue(dict, key):
    if dict:
        return dict.get(key)
    else:
        return
