from django.contrib.messages.api import error
from django_redis import get_redis_connection
from shop.models import ProductSKU


def cal_cart_count(user_id):
    """
    Get data from redis and calculate types of products in the shopping cart
    """
    conn = get_redis_connection('cart')
    cart_key = f'cart_{user_id}'
    cart_count = conn.hlen(cart_key)
    return cart_count


def cal_total_count_subtotal(user_id):
    """
    Calculate total items count in the cart and subtotal price from redis, 
    return products list, total items count and subtotal amount.
    Add temporary attribute amount and count to product objects for page rendering.
    """
    try:
        conn = get_redis_connection('cart')

        cart_key = f'cart_{user_id}'
        cart_dict = conn.hgetall(cart_key)

        products = []
        total_count = 0
        subtotal = 0
        for product_id, count in cart_dict.items():
            product = ProductSKU.objects.get(id=product_id)
            amount = product.price * int(count)
            product.amount = amount
            product.count = int(count)
            products.append(product)

            total_count += int(count)
            subtotal += amount

        return products, total_count, subtotal
    except:
        return [], 0, 0


def delete_cart_item(user_id, sku_id):
    """
    Delete selected item from shopping cart, return total items count for update
    """
    try:
        conn = get_redis_connection('cart')
        cart_key = f'cart_{user_id}'

        conn.hdel(cart_key, sku_id)
    except:
        pass


def cal_shipping_fee(subtotal, total_count):
    """ Shipping fee calculation simplified as much as possible """
    if subtotal > 10000:
        shipping_fee = 0
    else:
        shipping_fee = total_count * 500
    return shipping_fee
