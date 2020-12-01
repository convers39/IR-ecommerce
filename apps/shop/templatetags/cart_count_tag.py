from django import template
from django_redis import get_redis_connection

register = template.Library()


@register.simple_tag
def cart_count(request):
    """
    Custom tag approach to pass context data to base template.
    More efective way to acheive this by using context processor.
    Context processor must take a http request as arg, 
    should consider to use tag when request is not required.
    """
    user = request.user
    conn = get_redis_connection('cart')
    try:
        _count = conn.hlen(f'cart_{user.id}')
        if int(_count) <= 0:
            _count = 0
    except:
        _count = 0
    return int(_count)
