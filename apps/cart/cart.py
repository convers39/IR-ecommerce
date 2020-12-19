import uuid
from django_redis import get_redis_connection
from django.db.models import Case, When
from shop.models import ProductSKU

conn = get_redis_connection('cart')


def cal_cart_count(user_id):
    """
    Get data from redis and calculate types of products in the shopping cart
    """
    cart_key = f'cart_{user_id}'
    cart_count = conn.hlen(cart_key)
    return cart_count


def get_cart_all_in_order(user_id):
    """
    Return all key value pairs in current shopping cart and the order
    Ordering can be used in filter queries to keep the order of cart
    """
    # hgetall returns a dictionary {sku_id:count}, expand keys and values to list
    cart_dict = conn.hgetall(f'cart_{user_id}')
    # or use higher-order function [*map(int,[*cart_dict])]
    sku_ids = [int(i) for i in [*cart_dict]]
    counts = [int(c) for c in [*cart_dict.values()]]

    """HIGHLIGHT: Dynamite super trick from Django ORM magic"""
    ordering = Case(*[When(pk=pk, then=pos)
                      for pos, pk in enumerate(sku_ids)])
    return sku_ids, counts, ordering


def cal_total_count_subtotal(user_id):
    """
    Calculate total items count in the cart and subtotal price from redis, 
    return products list, total items count and subtotal amount.
    Add temporary attribute amount and count to product objects for page rendering.
    """
    try:
        sku_ids, counts, ordering = get_cart_all_in_order(user_id)
        products = ProductSKU.objects.filter(id__in=sku_ids).order_by(ordering)

        total_count = 0
        subtotal = 0
        for product, count in zip(products, counts):
            amount = product.price * count
            product.amount = amount
            product.count = count

            total_count += count
            subtotal += amount

        return products, total_count, subtotal
    except:
        return [], 0, 0


def delete_cart_item(user_id, sku_id):
    """
    Delete selected item from shopping cart, return total items count for update
    """
    try:
        cart_key = f'cart_{user_id}'
        conn.hdel(cart_key, sku_id)
    except:
        print('Item not found in cart')


def cal_shipping_fee(subtotal, total_count):
    """ Shipping fee calculation simplified as much as possible """
    if subtotal > 10000:
        shipping_fee = 0
    else:
        shipping_fee = total_count * 500
    return shipping_fee


def get_user_id(request):
    if request.user.is_authenticated:
        user_id = request.user.id
    else:
        # get cookie uuid else create new
        try:
            user_id = request.COOKIES['uuid']
        except KeyError:
            user_id = str(uuid.uuid4())
    return user_id


def is_first_time_guest(request):
    return (not request.user.is_authenticated) and (not request.COOKIES.get('uuid'))


def get_watch_history_products(user_id):
    """ Return a queryset with recent watched products """

    sku_ids = conn.lrange(f'history_{user_id}', 0, 7)
    ordering = Case(*[When(pk=pk, then=pos)
                      for pos, pk in enumerate(sku_ids)])
    # NOTE: Use forloop will create duplicate queries
    recent_products = ProductSKU.objects.filter(
        id__in=sku_ids).order_by(ordering)
    return recent_products
