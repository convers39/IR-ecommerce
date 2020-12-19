from django_redis import get_redis_connection
from cart.cart import get_user_id

from .models import Category


def base_template_data_processor(request):
    user_id = get_user_id(request)
    categories = Category.objects.all()

    conn = get_redis_connection('cart')
    cart_count = conn.hlen(f'cart_{user_id}')
    wishlist_count = 0
    if request.user.is_active:
        wishlist_count = conn.scard(f'wish_{user_id}')

    return {
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
        'categories': categories,
    }
