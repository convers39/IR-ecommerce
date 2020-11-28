from django.core.checks import messages
from django.shortcuts import render, redirect
from django.urls.base import reverse, reverse_lazy
from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db import transaction
from django.conf import settings

from django_redis import get_redis_connection

import stripe
import json
from shop.models import ProductSKU
from account.models import Address
from cart.cart import cal_total_count_subtotal, cal_shipping_fee

from .models import Order, Payment, OrderProduct
from .mixins import OrderDataCheckMixin
from .utils import generate_order_number

# Create your views here.


class CheckoutView(LoginRequiredMixin, View):
    """
    Retrieve data from redis and render a checkout confirmation page
    """

    def get(self, request):
        user = request.user

        conn = get_redis_connection('cart')
        cart_key = f'cart_{user.id}'

        cart_count = conn.hlen(cart_key)
        if cart_count == 0:
            messages.warning(request, 'Cart is empty')
            return redirect(reverse('cart:info'))

        products, total_count, subtotal = cal_total_count_subtotal(user.id)

        # shipping should be an independant module in a more complex project
        shipping_fee = cal_shipping_fee(subtotal, total_count)

        total_price = subtotal + shipping_fee

        addrs = Address.objects.filter(user=user)

        stripe_api_key = settings.STRIPE_PUBLIC_KEY

        context = {'products': products,
                   'total_count': total_count,
                   'cart_count': cart_count,
                   'subtotal': subtotal,
                   'shipping_fee': shipping_fee,
                   'total_price': total_price,
                   'addrs': addrs,
                   'stripe_api_key': stripe_api_key,
                   }

        return render(request, 'order/checkout.html', context)


class OrderProcessView(OrderDataCheckMixin, View):
    """
    Create an Order instance when accept an ajax request from checkout page, 
    create a stripe checkout session, response a json containing sessionId,
    and in the fronend use this sessionId to redirect customer to stripe checkout
    """

    @transaction.atomic
    def post(self, request):
        # retreive data from request
        user = request.user

        data = json.loads(request.body.decode())
        addr_id = data.get('addr').split('-')[-1]
        payment_method = data.get('payment_method')

        products, total_count, subtotal = cal_total_count_subtotal(user.id)
        shipping_fee = cal_shipping_fee(subtotal, total_count)

        sku_ids = ','.join(str(product.id) for product in products)
        sku_ids = sku_ids.split(',')

        # make transaction savepoint before changing any data in database
        save_id = transaction.savepoint()
        try:
            # create an Order instance
            address = Address.objects.get(id=addr_id)
            order = Order.objects.create(
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                user=user,
                address=address
            )

            # create OrderProduct instance for earch sku
            conn = get_redis_connection('cart')
            for sku_id in sku_ids:
                sku = ProductSKU.objects.get(sku_id)
                count = conn.hget(f'cart_{user.id}', sku_id)
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 0, 'errmsg': f'Item {sku.name} understocked'})

                OrderProduct.objects.create(
                    order=order,
                    sku=sku,
                    count=count,
                    unit_price=sku.price
                )
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

            # create stripe checkout session
            price = order.total_amount
            products = order.products
            name = f'{products.first()} and other {products.count()} items' \
                if len(sku_ids) > 1 else products.first()
            session = stripe.checkout.Session.create(
                payment_method_types=[f'{payment_method}'],
                customer_email=user.email,
                line_items=[{
                    'price_data': {
                        'currency': 'jpy',
                        'product_data': {
                            'name': name,
                        },
                        'unit_amount': price,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=reverse_lazy('order:success'),
                cancel_url=reverse_lazy('account:center'),
            )

            # create Payment instance
            payment_intent = session.payment_intent
            payment = Payment.objects.create(
                number=payment_intent,
                amount=price,
                method=payment_method,
                user=user,
                session_id=session.id
            )
            order.payment = payment
            order.save()

            # change payment status to succeeded
            payment.pay()
        except:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 0, 'errmsg': 'Failed to create order'})

        # commitpt all changes to database
        transaction.savepoint_commit(save_id)

        # clear shopping cart in the end
        conn.hdel(f'cart_{user.id}', *sku_ids)

        return JsonResponse({'res': 1, 'msg': 'Order created', 'session': session})


class PaymentSuccessView(TemplateView):
    template_name = 'order/success.html'

    def get(self, request):
        user = request.user
        payment = user.payments.first()

        if payment.status != 'SC':
            messages.error(request, 'Invalid visit')
            return redirect(reverse('shop:index'))

        return render(request, self.template_name, {'payment_number': payment.number})
