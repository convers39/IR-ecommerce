from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls.base import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import View, TemplateView

import stripe
import json
from datetime import datetime, timedelta, timezone

from django_redis import get_redis_connection

from account.models import Address
from shop.models import ProductSKU
from cart.cart import cal_total_count_subtotal, cal_shipping_fee, cal_cart_count

from .models import Order, Payment, OrderProduct
from .mixins import OrderDataCheckMixin, OrderManagementMixin


stripe.api_key = settings.STRIPE_SECRET_KEY


class OrderProcessView(OrderDataCheckMixin, View):
    """
    Customer click place order to send an ajax request,
    recieve address and payment method only from request data,
    retrieve shopping cart data from redis and calculate price,
    add lock when retrieve product data from DB (using pessimistic lock here), 
    create a stripe checkout session, response a json containing sessionId,
    and in the fronend use the sessionId to redirect customer to stripe checkout
    """

    @transaction.atomic
    def post(self, request):
        # retreive data from request
        user = request.user
        data = json.loads(request.body.decode())
        addr_id = data.get('addr_id')
        payment_method = data.get('payment_method')

        # make transaction savepoint before changing any data in database
        save_id = transaction.savepoint()
        try:
            # create an Order instance
            address = Address.objects.get(id=addr_id)
            order = Order.objects.create(
                subtotal=0,
                user=user,
                address=address
            )
            print('order created')

            # create OrderProduct instance for earch product
            conn = get_redis_connection('cart')
            cart_dict = conn.hgetall(f'cart_{user.id}')

            products = []
            total_count = subtotal = 0
            for sku_id, count in cart_dict.items():
                try:
                    # add lock when retrieve product data
                    product = ProductSKU.objects.select_for_update().get(id=sku_id)
                except ProductSKU.DoesNotExist:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 0, 'errmsg': 'Item does not exist'})

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

                products.append(product)
                total_count += int(count)
                subtotal += product.price * int(count)
            print('orderproducts created')

            # update shipping fee and subtotal in order object
            shipping_fee = cal_shipping_fee(subtotal, total_count)
            order.shipping_fee = shipping_fee
            order.subtotal = subtotal
            print('order updated')

            # create stripe checkout session, keep 1 item only
            amount = order.total_amount
            item_name = f'{products[0].name} and other {len(products)-1} items' \
                if len(products) > 2 else f'{products[0].name},{products[1].name}'
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

        # committ all changes to database
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
        # TODO: add order number into url
        success_url='http://127.0.0.1:8080/order/success/?session_id={CHECKOUT_SESSION_ID}',
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
        orders = payment.orders.all()
        context = {'payment_number': payment.number, 'orders': orders}

        time_delta = datetime.now(tz=timezone.utc) - payment.created_at
        if payment.status != 'SC' or time_delta > timedelta(minutes=5):
            messages.error(request, 'Invalid access')
            return redirect(reverse('account:order-list'))

        return render(request, self.template_name, context)


@require_POST
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
    payment = Payment.objects.get(
        number=session.payment_intent).prefetch_related('orders')
    payment.pay()
    payment.save()
    for order in payment.orders.all():
        order.confirm()
        order.save()


class PaymentRenewView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})
        print(data)

        order_id = data.get('order_id')
        order = Order.objects.select_related('payment').get(id=order_id)
        payment = order.payment
        method = payment.method
        name = f'Retry payment for order# {order.number}'
        amount = payment.amount
        try:
            session = create_checkout_session(
                user, method, name, amount)
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Failed to renew payment session'})

        payment.renew_payment(session)
        return JsonResponse({
            'res': '1',
            'session': session,
            'msg': 'Payment session renewed'
        })


class OrderCancelView(OrderManagementMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode())
        order = Order.objects.get(id=data['order_id'])

        status = order.status
        if status == 'SP':
            order.request_return()
            order.save()
            return JsonResponse({'res': '1', 'msg': 'Return request has been sent'})

        elif status == 'CF':
            order.request_cancel()
            order.save()
            return JsonResponse({'res': '1', 'msg': 'Cancel request has been sent'})

        elif status == 'NW':
            order.auto_cancel()
            order.save()
            order.restore_product_stock()
            return JsonResponse({'res': '1', 'msg': 'Your order has been cancelled'})

        elif status == 'CL':
            order.stop_cancel_request()
            order.save()
            return JsonResponse({'res': '1', 'msg': 'Cancel request stopped'})

        elif status == 'RT':
            order.stop_return_request()
            order.save()
            return JsonResponse({'res': '1', 'msg': 'Return request stopped'})

        else:
            return JsonResponse({'res': '0', 'errmsg': f'Order at {order.status} cannot be cancelled'})


class OrderDeleteView(OrderManagementMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode())
        order = Order.objects.get(id=data['order_id'])
        order.is_deleted = True  # similar as 'hided by user', still available in database
        order.save()
        return JsonResponse({'res': '1', 'msg': 'Order deleted'})
