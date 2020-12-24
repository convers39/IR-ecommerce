from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models.query_utils import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls.base import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import View, TemplateView, ListView

import json
import logging
from datetime import datetime, timedelta, timezone

import stripe
from django_redis import get_redis_connection

from account.models import User
from account.tasks import send_order_email
from cart.cart import cal_shipping_fee, get_user_id, get_cart_all_in_order
from shop.models import ProductSKU

from .mixins import OrderProcessCheckMixin, OrderManagementMixin, OrderReviewDataMixin
from .models import Order, Payment, OrderProduct, Review
# from .tasks import create_one_time_task


stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


class OrderProcessView(OrderProcessCheckMixin, View):
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
        data = json.loads(request.body.decode())
        payment_method = data.get('payment_method')
        user, address = self.get_user_and_address()

        # make transaction savepoint before changing any data in database
        save_id = transaction.savepoint()
        try:
            # create an Order instance
            order = Order.objects.create(
                subtotal=0, user=user, address=address)
            logger.info(f'order# {order.number} created')

            # get shopping cart cart data
            user_id = get_user_id(request)
            conn = get_redis_connection('cart')
            sku_ids, counts, ordering = get_cart_all_in_order(user_id)

            # add lock when retrieve product data
            try:
                products = ProductSKU.objects.select_for_update().filter(
                    id__in=sku_ids).order_by(ordering)
            except ProductSKU.DoesNotExist:
                transaction.savepoint_rollback(save_id)
                return JsonResponse({'res': 0, 'errmsg': 'Item does not exist'})

            for product, count in zip(products, counts):
                if count > product.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 0, 'errmsg': f'Item {product.name} understocked'})
                product.stock -= count
                product.sales += count
            # update products stock and sales
            ProductSKU.objects.bulk_update(products, ['stock', 'sales'])
            logger.info(f'order# {order.number} product stock, sales updated')

            # create OrderProduct instance for earch product
            OrderProduct.objects.bulk_create([
                OrderProduct(order=order, product=product,
                             count=count, unit_price=product.price)
                for product, count in zip(products, counts)
            ])
            logger.info(f'order# {order.number} orderproducts created')

            # update shipping fee and subtotal in order object
            subtotal = sum([product.price*count for product,
                            count in zip(products, counts)])
            total_count = sum(counts)
            shipping_fee = cal_shipping_fee(subtotal, total_count)
            order.shipping_fee = shipping_fee
            order.subtotal = subtotal
            logger.info(
                f'order# {order.number} subtotal, shipping fee updated ')

            # create stripe checkout session, keep 1 item only
            amount = order.total_amount
            item_name = f'{products[0].name} ({len(products)} items in total)' \
                if len(products) > 1 else f'{products[0].name}'

            try:
                session = create_checkout_session(
                    user, payment_method, item_name, amount)
            except:
                transaction.savepoint_rollback(save_id)
                return JsonResponse({'res': 0, 'errmsg': 'Failed to create payment session'})
            logger.info(f'order# {order.number} checkout session created')

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
            logger.info(
                f'order# {order.number} payment instance {payment.number} created')

        except:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 0, 'errmsg': 'Failed to create order'})

        # committ all changes to database
        transaction.savepoint_commit(save_id)

        # clear shopping cart in the end
        conn.hdel(f'cart_{user_id}', *sku_ids)
        logger.info(
            f'order# {order.number} processed, user {user.username} cart cleared')

        # send email to user
        send_order_email.delay(user.email, user.username,
                               order.number, order.status)
        # start a periodic task for 24/48 hrs later to check the payment status
        # create_one_time_task()

        return JsonResponse({'res': 1, 'msg': 'Order created', 'session': session})


def create_checkout_session(user, payment_method, item_name, amount):
    domain = 'http://127.0.0.1:8080'
    cancel_url = domain + reverse('shop:index')
    success_url = domain + reverse('order:success') + \
        '?session_id={CHECKOUT_SESSION_ID}'
    if user.is_authenticated:
        cancel_url = domain + reverse('account:order')

    try:
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
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session
    except:
        raise Exception('Error on creating payment session')


class PaymentSuccessView(TemplateView):
    template_name = 'order/success.html'

    def get(self, request):
        user_id = get_user_id(request)
        if request.user.is_authenticated:
            user = User.objects.get(id=user_id)
            url = reverse('account:order')
        else:
            guest_name = f'guest_{user_id}'
            user = User.objects.get(username=guest_name)
            url = reverse('order:search')

        session_id = request.GET.get('session_id')
        try:
            payment = user.payments.get(session_id=session_id)
        except:
            messages.error(request, 'Payment not found')
            return redirect(url)

        time_delta = datetime.now(tz=timezone.utc) - payment.created_at
        if payment.status != 'SC' or time_delta > timedelta(minutes=10):
            messages.error(request, 'Invalid access')
            return redirect(url)

        orders = payment.orders.all()
        context = {'payment_number': payment.number, 'orders': orders}
        return render(request, self.template_name, context)


@require_POST
@csrf_exempt
def checkout_webhook(request):
    print('event received, processing...')
    endpoint_secret = settings.WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    # print('webhook', payload, sig_header, endpoint_secret)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        print(event['type'])
    except ValueError as e:
        # Invalid payload
        print('invalid payload')
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print('invalid signature')
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        fulfill_order(session.payment_intent)
    # Passed signature verification
    return HttpResponse(status=200)


def fulfill_order(intent_id):
    # change payment status to succeeded, order status to confirmed
    payment = Payment.objects.prefetch_related('orders').select_related('user').get(
        number=intent_id)
    user = payment.user
    payment.pay()
    payment.save()
    for order in payment.orders.all():
        order.confirm()
        order.save()  # status New to Confirmed
        send_order_email.delay(user.email, user.username,
                               order.number, order.status)


class PaymentRenewView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})
        print(data)

        order_id = data.get('order_id')
        order = Order.objects.select_related('payment')\
            .prefetch_related('order_products__product').get(id=order_id)
        payment = order.payment
        method = payment.method
        # name = f'Retry payment for order# {order.number}'
        products = [op.product.name for op in order.order_products.all()]
        name = f'{products[0].name} ({len(products)} items in total)' \
            if len(products) > 1 else f'{products[0].name}'
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
            send_order_email.delay(
                order.user.email, order.user.username, order.number, order.status)
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

    def delete(self, request, *args, **kwargs):
        data = json.loads(request.body.decode())
        order = Order.objects.get(id=data['order_id'])
        order.is_deleted = True  # similar as 'hided by user', still available in database
        order.save()
        return JsonResponse({'res': '1', 'msg': 'Order deleted'})


class OrderSearchView(ListView):
    """
    This view only use for guests to check their order status,
    a login user will not see the link in the nav bar and will be 
    redirected to account center if visited.
    """
    model = Order
    template_name = 'order/search.html'
    context_object_name = 'orders'

    def get(self, request, *args, **kwargs) -> HttpResponse:
        if self.request.user.is_authenticated:
            return redirect(reverse('account:order'))
        return super().get(request, *args, **kwargs)

    def get_queryset(self):

        email = self.request.GET.get('email')
        order_number = self.request.GET.get('order_number')

        if email == order_number == None:
            return None

        if not all([email, order_number]):
            messages.error(
                self.request, 'Both email and order number are required')
            return None

        queryset = super().get_queryset().prefetch_related('order_products__product')\
            .select_related(*['payment', 'user']).filter(number=order_number)

        # in case the guest registered an account and email was changed
        user = User.objects.filter(
            Q(email__endswith=email) | Q(email=email)).first()
        if not user:
            messages.error(self.request, 'Incorrect email')
            return None

        if len(queryset) == 0:
            messages.error(self.request, 'order number does not exist')
        elif queryset[0].user != user:
            queryset = queryset.none()
            messages.error(self.request, 'order and email does not match')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_key'] = settings.STRIPE_PUBLIC_KEY
        return context


class OrderCommentView(OrderReviewDataMixin, View):

    def update(self, request, *args, **kwargs):
        pass

    def delete(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode())
        op_id = data.get('op_id')
        order_product = OrderProduct.objects.get(id=op_id)

        Review.objects.create(
            order_product=order_product,
            star=data['star'],
            comment=data['comment']
        )
        return JsonResponse({'res': '1', 'msg': 'Comment submitted'})
