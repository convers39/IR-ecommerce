from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from django.urls.base import reverse

import json
from django_redis import get_redis_connection

from account.models import Address
from account.forms import GuestAddressForm, AddressForm
from shop.models import ProductSKU

from .cart import (cal_cart_count, cal_total_count_subtotal,
                   delete_cart_item, cal_shipping_fee, get_user_id, is_first_time_guest)
from .mixins import DataIntegrityCheckMixin


class CartAddView(DataIntegrityCheckMixin, View):
    """
    Use in Index, List, Detail pages for 'add to cart' button event.
    Receive ajax request, validate data, save product id and count to redis
    datatype: hash, format: cart_<user_id>:{<sku_id>:<count>}
    """

    def post(self, request):

        user_id = get_user_id(request)

        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = int(data.get('count'))

        conn = get_redis_connection('cart')
        cart_key = f'cart_{user_id}'
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            count += int(cart_count)

        stock = ProductSKU.objects.get(id=sku_id).stock
        if count > stock:
            return JsonResponse({'res': 0, 'errmsg': 'Understocked'})

        conn.hset(cart_key, sku_id, count)
        cart_count = conn.hlen(cart_key)
        print('add', cart_count)

        response = JsonResponse({
            'res': 1,
            'msg': 'Added to cart',
            'cart_count': cart_count,
        })
        # set uuid cookie for guest user
        if is_first_time_guest(request):
            response.set_cookie('uuid', user_id, max_age=3600*24*7)
        return response


class CartInfoView(View):
    """
    Retrieve data from redis and render current shopping cart page,
    """

    def get(self, request, *args, **kwargs):
        user_id = get_user_id(request)
        print('user_id', user_id)
        products, total_count, subtotal = cal_total_count_subtotal(user_id)

        context = {
            'total_count': total_count,
            'subtotal': subtotal,
            'products': products,
        }
        print(context)
        return render(request, 'cart/cart.html', context)


class CartUpdateView(DataIntegrityCheckMixin, View):
    """
    Correspond with inc and dec button click event,
    and item count manual input blur event in cart page,
    var count will be the updated count number instead of previous count.
    """

    def post(self, request):

        # user = request.user
        user_id = get_user_id(request)

        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')

        # connect redis, reset product count
        conn = get_redis_connection('cart')
        cart_key = f'cart_{user_id}'

        conn.hset(cart_key, sku_id, count)

        return JsonResponse({
            'res': 1,
            'msg': 'Cart updated',
            'sku_id': sku_id,
            'count': count
        })


class CartDeleteView(DataIntegrityCheckMixin, View):

    def post(self, request):

        user_id = get_user_id(request)

        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')

        delete_cart_item(user_id, sku_id)
        cart_count = cal_cart_count(user_id)

        return JsonResponse({
            'res': 1,
            'msg': 'Item deleted',
            'cart_count': cart_count
        })


class CheckoutView(View):
    """
    Retrieve data from redis and render a checkout confirmation page
    """

    def get(self, request):
        # user = request.user
        user_id = get_user_id(request)

        form = GuestAddressForm()
        # formset = create_address_formset(user)

        cart_count = cal_cart_count(user_id)
        if cart_count == 0:
            messages.error(request, 'Cart is empty')
            return redirect(reverse('cart:info'))

        products, total_count, subtotal = cal_total_count_subtotal(user_id)

        # shipping should be an independant module in a more complex project
        shipping_fee = cal_shipping_fee(subtotal, total_count)
        total_price = subtotal + shipping_fee

        if shipping_fee == 0:
            shipping_fee = 'Free'

        addrs = []
        if request.user.is_authenticated:
            form = AddressForm()
            addrs = Address.objects.filter(user=request.user)

        stripe_api_key = settings.STRIPE_PUBLIC_KEY

        context = {'products': products,
                   'addrs': addrs,
                   'shipping_fee': shipping_fee,
                   'subtotal': subtotal,
                   'total_count': total_count,
                   'total_price': total_price,
                   'stripe_api_key': stripe_api_key,
                   'form': form,
                   #    'formset': formset
                   }

        return render(request, 'cart/checkout.html', context)
