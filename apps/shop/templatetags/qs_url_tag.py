from django import template

register = template.Library()


@register.simple_tag
def qs_url(field_name, value, urlencode=None):
    get_query = f'?{field_name}={value}'
    if urlencode:
        qs = urlencode.split('&')
        _filtered = filter(lambda p: p.split('=')[0] != field_name, qs)
        querystring = '&'.join(_filtered)
        get_query = f'{get_query}&{querystring}'
    return get_query
