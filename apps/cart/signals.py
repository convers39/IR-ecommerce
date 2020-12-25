from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from django_redis import get_redis_connection


@receiver(user_logged_in)
def merge_shopping_cart(sender, user, request,  **kwargs):
    """
    Check if there are items in shopping cart before login,
    merge guest shopping cart to user cart and remove guest cart data
    uuid cookie will be expired in 7 days
    """
    try:
        uuid = request.COOKIES['uuid']
        conn = get_redis_connection('cart')

        user_key = f'cart_{user.id}'
        guest_key = f'cart_{uuid}'
        guest_cart = conn.hgetall(guest_key)
        user_cart = conn.hgetall(user_key)
        updated_cart = {**guest_cart, **user_cart}
        # user_cart |= guest_cart  # new in python3.9+
        # NOTE: this merge will overwrite the count of same product with user cart data
        conn.hset(user_key, mapping=updated_cart)
        conn.delete(guest_key)
    except:
        # no uuid found, do nothing
        return
