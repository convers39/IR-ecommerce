from apps.cart.cart import cal_cart_count
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls.base import reverse, reverse_lazy
from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
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


stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutView(LoginRequiredMixin, View):
    """
    Retrieve data from redis and render a checkout confirmation page
    """

    def get(self, request):
        user = request.user

        cart_count = cal_cart_count(user.id)
        if cart_count == 0:
            messages.error(request, 'Cart is empty')
            return redirect(reverse('cart:info'))

        products, total_count, subtotal = cal_total_count_subtotal(user.id)

        # shipping should be an independant module in a more complex project
        shipping_fee = cal_shipping_fee(subtotal, total_count)
        total_price = subtotal + shipping_fee

        if shipping_fee == 0:
            shipping_fee = 'Free'

        addrs = Address.objects.filter(user=user)

        stripe_api_key = settings.STRIPE_PUBLIC_KEY

        context = {'products': products,
                   'addrs': addrs,
                   'shipping_fee': shipping_fee,
                   'subtotal': subtotal,
                   'total_count': total_count,
                   'total_price': total_price,
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
            print('order created')

            # create OrderProduct instance for earch product
            conn = get_redis_connection('cart')
            for product in products:
                count = conn.hget(f'cart_{user.id}', product.id)
                if int(count) > product.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 0, 'errmsg': f'Item {product.name} understocked'})

                OrderProduct.objects.create(
                    order=order,
                    product=product,
                    count=int(count),
                    unit_price=product.price
                )
                product.stock -= int(count)
                product.sales += int(count)
                product.save()
            print('orderproducts created')

            # create stripe checkout session, keep 1 item only
            amount = order.total_amount
            item_name = f'{products[0].name} and other {len(products)} items' \
                if len(products) > 1 else f'{products[0].name}'
            session = create_checkout_session(
                user, payment_method, item_name, amount)
            print('checkout session created')

            # create Payment instance
            payment = Payment.objects.create(
                number=session.payment_intent,
                amount=amount,
                method=payment_method,
                user=user,
                session_id=session.id
            )
            order.payment = payment
            order.save()
            print('payment created')

        except:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 0, 'errmsg': 'Failed to create order'})

        # commitpt all changes to database
        transaction.savepoint_commit(save_id)

        # clear shopping cart in the end
        conn.hdel(f'cart_{user.id}', *[product.id for product in products])
        print('shopping cart cleared')

        return JsonResponse({'res': 1, 'msg': 'Order created', 'session': session})


def create_checkout_session(user, payment_method, item_name, amount):
    session = stripe.checkout.Session.create(
        payment_method_types=[payment_method],
        customer_email=user.email,
        line_items=[{
            'price_data': {
                'currency': 'jpy',
                'product_data': {
                    'name': item_name,
                },
                'unit_amount': int(amount),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://127.0.0.1:8080/order/success/',
        cancel_url='http://127.0.0.1:8080/account/order/',
        # success_url=reverse('order:success'),
        # cancel_url=reverse('account:center'),
    )
    return session


class PaymentSuccessView(TemplateView):
    template_name = 'order/success.html'

    def get(self, request):
        user = request.user
        payment = user.payments.first()

        if payment.status != 'SC':
            messages.error(request, 'Invalid visit')
            return redirect(reverse('shop:index'))

        return render(request, self.template_name, {'payment_number': payment.number})


@csrf_exempt
def checkout_webhook(request):
    endpoint_secret = settings.WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        fulfill_order(session)
    # Passed signature verification
    return HttpResponse(status=200)


def fulfill_order(session):
    # change payment status to succeeded, order status to confirmed
    payment = Payment.objects.get(number=session.payment_intent)
    payment.pay()
    payment.save()
    for order in payment.orders.all():
        order.confirm_payment()
        order.save()
