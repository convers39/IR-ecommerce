from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin


from django_redis import get_redis_connection

from shop.models import ProductSKU, Category
# import json
from .cart import cal_cart_count, cal_total_count_subtotal, delete_cart_item
from .mixins import DataIntegrityCheckMixin

# Create your views here.


class CartAddView(DataIntegrityCheckMixin, View):
    """
    Use in Index, List, Detail pages for 'add to cart' button event.
    Receive ajax request, validate data, save product id and count to redis
    datatype: hash, format: cart_<user_id>:{<sku_id>:<count>}
    """

    def post(self, request):

        user = request.user
        sku_id = request.POST.get('sku_id')
        count = int(request.POST.get('count'))

        conn = get_redis_connection('cart')
        cart_key = f'cart_{user.id}'
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            count += int(cart_count)

        stock = ProductSKU.objects.get(id=sku_id).stock
        if count > stock:
            return JsonResponse({'res': 0, 'errmsg': 'Understocked'})

        conn.hset(cart_key, sku_id, count)
        cart_count = conn.hlen(cart_key)
        print('add', cart_count)

        return JsonResponse({'res': 1, 'cart_count': cart_count, 'msg': 'Added to cart'})


class CartInfoView(LoginRequiredMixin, View):
    """
    Retrieve data from redis and render current shopping cart
    """

    def get(self, request):
        user = request.user

        cart_count = cal_cart_count(user.id)
        print('infoview', cart_count)
        products, total_count, subtotal = cal_total_count_subtotal(user.id)

        categories = Category.objects.all()

        context = {
            'total_count': total_count,
            'subtotal': subtotal,
            'cart_count': cart_count,
            'products': products,
            'categories': categories,
        }

        return render(request, 'cart/cart.html', context)


class CartUpdateView(DataIntegrityCheckMixin, View):
    """
    Correspond with inc and dec button click event in cart page,
    either increase or decrease selected product count in the cart.
    """

    def post(self, request):

        user = request.user
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # connect redis, reset product count
        conn = get_redis_connection('cart')
        cart_key = f'cart_{user.id}'

        if int(count) <= 0:
            count = 1

        conn.hset(cart_key, sku_id, count)

        return JsonResponse({'res': 1, 'msg': 'Cart updated'})


class CartDeleteView(DataIntegrityCheckMixin, View):
    def post(self, request):

        user = request.user
        sku_id = request.POST.get('sku_id')

        delete_cart_item(user.id, sku_id)

        return JsonResponse({'res': 1, 'msg': 'Item deleted'})
