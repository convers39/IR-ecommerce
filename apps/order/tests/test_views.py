from datetime import datetime
from django.test import TestCase, Client
from django.test.client import FakePayload
from django.urls import reverse
from django.contrib.messages import get_messages
from django.db.models.signals import post_save

from django_redis import get_redis_connection
import factory

from account.tests.factory import UserFactory, AddressFactory
from shop.tests.factory import SkuFactory
from order.tests.factory import OrderFactory, OrderProductFactory, PaymentFactory
from order.views import (OrderProcessView, PaymentSuccessView)
from order.models import Order, Payment, OrderProduct, Review
from shop.models import ProductSKU


class TestOrderProcessView(TestCase):

    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse('order:process')
        cls.user = UserFactory()
        cls.address = AddressFactory()
        cls.key = f'cart_{cls.user.id}'
        cls.conn = get_redis_connection('cart')
        cls.payload = {'addr_id': cls.address.id,
                       'payment_method': 'card'}
        cls.content_type = 'application/json'

    def tearDown(self) -> None:
        get_redis_connection('cart').flushdb()
        get_redis_connection('default').flushdb()

    def test_process_order_success(self):
        self.client.force_login(self.user)
        payload = {'addr_id': self.address.id,
                   'payment_method': 'card'}
        skus = []
        with factory.django.mute_signals(post_save):
            for _ in range(3):
                sku = SkuFactory(price=5000)
                skus.append(sku)
                self.conn.hset(self.key, sku.id, 1)

        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.resolver_match.func.__name__,
                         OrderProcessView.as_view().__name__)
        self.assertEqual(res_data['res'], 1)
        self.assertEqual(res_data['msg'], 'Order created')
        self.assertContains(res, 'session')
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(OrderProduct.objects.count(), 3)
        self.assertEqual(self.conn.hlen(self.key), 0)

    # TODO: test guest checkout
    # def test_user_not_login(self):
    #     payload = FakePayload()
    #     res = self.client.post(self.url, data=payload,
    #                            content_type=self.content_type)
    #     res_data = res.json()

    #     self.assertEqual(res_data['res'], 0)
    #     self.assertEqual(res_data['errmsg'], 'Please login')
    # guest user only
    # def test_address_data_not_complete(self):
    #     pass

    def test_invalid_payload(self):
        payload = {'addr_id': self.address.id,
                   'payment_method': 'card'}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type='application/x-www-form-urlencoded')
        res_data = res.json()
        print(res.json())

        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Invalid data')

    def test_invalid_payment_method(self):
        payload = {'addr_id': self.address.id,
                   'payment_method': 'bitcoin'}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Invalid payment method')

    def test_cart_is_empty(self):
        user = UserFactory()
        payload = {'addr_id': self.address.id, 'payment_method': 'card'}
        self.client.force_login(user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Cart is empty')

    def test_address_not_exists(self):
        payload = {'addr_id': 666, 'payment_method': 'card'}
        sku = SkuFactory(price=5000)
        self.conn.hset(self.key, sku.id, 1)
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Address does not exist')

    def test_sku_not_exists(self):
        payload = {'addr_id': self.address.id,
                   'payment_method': 'card'}
        self.client.force_login(self.user)
        get_redis_connection('cart').flushdb()
        ProductSKU.objects.all().delete()

        skus = []
        for _ in range(3):
            sku = SkuFactory(price=5000)
            skus.append(sku)
            self.conn.hset(self.key, sku.id, 1)

        deleted_sku = ProductSKU.objects.first()
        deleted_sku.delete()
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.context
        print(res_data)
        msg = list(get_messages(res.wsgi_request))

        self.assertRedirects(res, '/cart/checkout/', 302, 200)
        self.assertEqual(str(msg[0]), 'Item does not exist')

    def test_sku_understocked(self):
        payload = {'addr_id': self.address.id,
                   'payment_method': 'card'}
        self.client.force_login(self.user)
        get_redis_connection('cart').flushdb()
        ProductSKU.objects.all().delete()

        skus = []
        for _ in range(3):
            sku = SkuFactory(price=5000, stock=2)
            skus.append(sku)
            self.conn.hset(self.key, sku.id, 10)

        understock_sku = ProductSKU.objects.first()
        understock_sku.stock = 1

        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        msg = list(get_messages(res.wsgi_request))

        self.assertRedirects(res, '/cart/checkout/', 302, 200)
        self.assertEqual(
            str(msg[0]), f'Item {understock_sku.name} understocked')


class TestPaymentSuccessView(TestCase):

    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory()
        cls.payment = PaymentFactory(user=cls.user, session_id='666666')
        cls.order = OrderFactory(user=cls.user, payment=cls.payment)
        cls.url = reverse('order:success') + '?session_id=666666'

    # FIXME: pass when run solo, fail when run with other tests
    def test_in_success_view(self):
        self.payment.pay()
        self.payment.save()
        self.client.force_login(self.user)
        res = self.client.get(self.url)

        print(res.context)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.payment.status, 'SC')
        self.assertIn('payment_number', res.context)
        self.assertIn('orders', res.context)
        self.assertTemplateUsed('order/success.html')
        self.assertEqual(res.resolver_match.func.__name__,
                         PaymentSuccessView.as_view().__name__)

    def test_payment_not_succeeded_redirect(self):
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        msg = list(get_messages(res.wsgi_request))

        self.assertRedirects(
            res, '/account/order/', 302, 200)
        self.assertEqual(str(msg[0]), 'Invalid access')

    def test_valid_period_expired_redirect(self):
        self.payment.created_at = datetime(2000, 10, 10, 10, 10, 10)
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        msg = list(get_messages(res.wsgi_request))

        self.assertRedirects(
            res, '/account/order/', 302, 200)
        self.assertEqual(str(msg[0]), 'Invalid access')

    def test_payment_not_found(self):
        self.payment.session_id = '55555'
        self.payment.save()
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        msg = list(get_messages(res.wsgi_request))

        self.assertRedirects(
            res, '/account/order/', 302, 200)
        self.assertEqual(str(msg[0]), 'Payment not found')

    # TODO: test guest checkout redirect


class TestPaymentRenewView(TestCase):
    pass


class TestOrderCancelView(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory()
        cls.url = reverse('order:cancel')
        cls.content_type = 'application/json'

    def test_request_return(self):
        order = OrderFactory(user=self.user, status='SP')
        self.client.force_login(self.user)
        payload = {'order_id': order.id}
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        order.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '1', 'msg': 'Return request has been sent'})
        self.assertEqual(order.status, 'RT')

    def test_request_cancel(self):
        order = OrderFactory(user=self.user, status='CF')
        self.client.force_login(self.user)
        payload = {'order_id': order.id}
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        order.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '1', 'msg': 'Cancel request has been sent'})
        self.assertEqual(order.status, 'CL')

    def test_auto_cancel(self):
        order = OrderFactory(user=self.user, status='NW')
        self.client.force_login(self.user)
        payload = {'order_id': order.id}
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        order.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '1', 'msg': 'Your order has been cancelled'})
        self.assertEqual(order.status, 'CX')

    def test_stop_cancel_request(self):
        order = OrderFactory(user=self.user, status='CL')
        self.client.force_login(self.user)
        payload = {'order_id': order.id}
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        order.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '1', 'msg': 'Cancel request stopped'})
        self.assertEqual(order.status, 'NW')

    def test_stop_return_request(self):
        order = OrderFactory(user=self.user, status='RT')
        self.client.force_login(self.user)
        payload = {'order_id': order.id}
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        order.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '1', 'msg': 'Return request stopped'})
        self.assertEqual(order.status, 'SP')

    def test_order_cannot_be_cancelled(self):
        order = OrderFactory(user=self.user, status='CP')
        self.client.force_login(self.user)
        payload = {'order_id': order.id}
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        order.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '0', 'errmsg': f'Order at {order.status} cannot be cancelled'})
        self.assertEqual(order.status, 'CP')

    def test_delete_order(self):
        order = OrderFactory(user=self.user, status='CX')
        self.client.force_login(self.user)
        payload = {'order_id': order.id}
        res = self.client.delete(self.url, data=payload,
                                 content_type=self.content_type)
        order.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '1', 'msg': 'Order deleted'})
        self.assertTrue(order.is_deleted)

    # TODO: test for guest


class TestOrderSearchView(TestCase):

    # TODO: figure out setting cookie
    def setUp(self) -> None:
        return super().setUp()

    @classmethod
    def setUpTestData(cls) -> None:
        return super().setUpTestData()

    def test_search_view_by_guest(self):
        pass

    def test_login_user_redirect(self):
        pass

    def test_submit_data_incomplete(self):
        pass

    def test_email_order_not_match(self):
        pass


class TestOrderCommentView(TestCase):

    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory()
        cls.order = OrderFactory(user=cls.user)
        cls.op = OrderProductFactory(order=cls.order)
        cls.url = reverse('order:comment')
        cls.content_type = 'application/json'

    def test_post_create_review(self):
        payload = {'op_id': self.op.id, 'star': '5',
                   'comment': 'awesome product'}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {'res': '1', 'msg': 'Comment submitted'})
        self.assertEqual(Review.objects.count(), 1)
        # self.assertEqual(str(msg[0]), 'Comment submitted')

    def test_comment_too_short(self):
        op = OrderProductFactory(order=self.order)
        payload = {'op_id': op.id, 'star': '5',
                   'comment': 'ok'}

        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '0', 'errmsg': 'Comment cannot be less than 10 characters'})
        self.assertEqual(Review.objects.count(), 0)

    def test_item_has_been_reviewed(self):
        op = OrderProductFactory(order=self.order)
        payload = {'op_id': op.id, 'star': '5',
                   'comment': 'good good item'}
        self.client.force_login(self.user)
        self.client.post(self.url, data=payload,
                         content_type=self.content_type)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '0', 'errmsg': 'You have already reviewed this item'})
        self.assertEqual(Review.objects.count(), 1)

    def test_incomplete_data(self):
        payload = {'star': '5', 'comment': 'good good item'}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '0', 'errmsg': 'Incompleted Data'})
        self.assertEqual(Review.objects.count(), 0)

    def test_post_item_not_exist(self):
        payload = {'op_id': '000', 'star': '5', 'comment': 'good good item'}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '0', 'errmsg': 'Item does not exist'})
        self.assertEqual(Review.objects.count(), 0)

    def test_invalid_data(self):
        payload = FakePayload()
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '0', 'errmsg': 'Invalid data'})
        self.assertEqual(Review.objects.count(), 0)
