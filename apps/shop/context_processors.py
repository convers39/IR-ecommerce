from .models import Category
from django_redis import get_redis_connection


def base_template_data_processor(request):
    user = request.user
    categories = Category.objects.all()

    if not user.is_authenticated:
        return {
            'wishlist_count': 0,
            'cart_count': 0,
            'categories': categories,
        }

    conn = get_redis_connection('cart')
    wishlist_count = conn.scard(f'wish_{user.id}')
    cart_count = conn.hlen(f'cart_{user.id}')

    return {
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
        'categories': categories,
    }
