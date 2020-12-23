from datetime import datetime
from apps.order.tests.factory import OrderFactory, PaymentFactory
import json
import pprint
from django.test import TestCase, Client, override_settings, TransactionTestCase, testcases
from django.test.client import FakePayload
from django.urls import resolve, reverse
from django.contrib.messages import get_messages
from django.db.models.signals import post_save

from django_redis import get_redis_connection
import factory

from account.tests.factory import UserFactory, AddressFactory
from shop.tests.factory import SkuFactory
from order.views import (OrderProcessView, PaymentSuccessView, checkout_webhook,
                         PaymentRenewView, OrderCancelView, OrderSearchView, OrderCommentView)
from order.models import Order, Payment, OrderProduct
from shop.models import ProductSKU


class TestOrderProcessView(TransactionTestCase):

    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse('order:process')
        cls.user = UserFactory()
        cls.address = AddressFactory()
        cls.key = f'cart_{cls.user.id}'
        cls.conn = get_redis_connection('cart')
        cls.payload = {'addr': f'addr-{cls.address.id}',
                       'payment_method': 'card'}
        cls.content_type = 'application/json'

    def tearDown(self) -> None:
        get_redis_connection('cart').flushdb()
        get_redis_connection('default').flushdb()

    def test_process_order_success(self):
        self.client.force_login(self.user)
        payload = {'addr': f'addr-{self.address.id}', 'payment_method': 'card'}
        skus = []
        with factory.django.mute_signals(post_save):
            for _ in range(3):
                sku = SkuFactory(price=5000)
                skus.append(sku)
                self.conn.hset(self.key, sku.id, 1)

        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = json.loads(res.content)

        self.assertEqual(res.resolver_match.func.__name__,
                         OrderProcessView.as_view().__name__)
        self.assertEqual(res_data['res'], 1)
        self.assertEqual(res_data['msg'], 'Order created')
        self.assertContains(res_data, 'session')
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(OrderProduct.objects.count(), 3)
        self.assertEqual(self.conn.hlen(self.key), 0)

    # TODO: test guest checkout
    # def test_user_not_login(self):
    #     payload = FakePayload()
    #     res = self.client.post(self.url, data=payload,
    #                            content_type=self.content_type)
    #     res_data = json.loads(res.content)

    #     self.assertEqual(res_data['res'], 0)
    #     self.assertEqual(res_data['errmsg'], 'Please login')

    def test_invalid_payload(self):
        payload = {'addr': f'addr-{self.address.id}', 'payment_method': 'card'}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type='application/x-www-form-urlencoded')
        res_data = json.loads(res.content)

        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Invalid data')

    def test_lack_of_data(self):
        payload = {'addr': f'addr-{self.address.id}'}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = json.loads(res.content)

        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Lack of data')

    def test_address_not_exists(self):
        payload = {'addr': 'addr-666', 'payment_method': 'card'}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = json.loads(res.content)

        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Address does not exist')

    def test_sku_not_exists(self):
        payload = {'addr': f'addr-{self.address.id}', 'payment_method': 'card'}
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
        res_data = json.loads(res.content)

        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Item does not exist')

    def test_sku_understocked(self):
        payload = {'addr': f'addr-{self.address.id}', 'payment_method': 'card'}
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
        res_data = json.loads(res.content)

        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'],
                         f'Item {understock_sku.name} understocked')


class TestPaymentSuccessView(TestCase):

    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory()
        cls.payment = PaymentFactory(user=cls.user)
        cls.order = OrderFactory(user=cls.user, payment=cls.payment)
        cls.url = reverse('order:success')

    def test_payment_not_succeeded_redirect(self):
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        msg = list(get_messages(res.wsgi_request))

        self.assertRedirects(res, '/account/order/', 302, 200)
        self.assertEqual(str(msg[0]), 'Invalid access')

    def test_valid_period_expired_redirect(self):
        self.payment.created_at = datetime(2000, 10, 10, 10, 10, 10)
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        msg = list(get_messages(res.wsgi_request))

        self.assertRedirects(res, '/account/order/', 302, 200)
        self.assertEqual(str(msg[0]), 'Invalid access')

    # TODO: test guest checkout redirect

    def test_success_view(self):
        self.payment.pay()
        self.payment.save()
        self.client.force_login(self.user)
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed('order/success.html')
        self.assertEqual(res.resolver_match.func.__name__,
                         PaymentSuccessView.as_view().__name__)


class TestPaymentRenewView(TestCase):
    pass


class TestOrderCancelView(TestCase):

    def setUp(self) -> None:
        return super().setUp()

    @classmethod
    def setUpTestData(cls) -> None:
        return super().setUpTestData()

    def test_request_return(self):
        pass

    def test_request_cancel(self):
        pass

    def test_auto_cancel(self):
        pass

    def test_stop_cancel_request(self):
        pass

    def test_stop_return_request(self):
        pass

    def test_order_cannot_be_cancelled(self):
        pass

    def test_delete_order(self):
        pass

# TODO: figure out setting cookie


class TestOrderSearchView(TestCase):

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
        return super().setUp()

    @classmethod
    def setUpTestData(cls) -> None:
        return super().setUpTestData()

    def test_post_create_review(self):
        pass

    def test_post_item_not_exist(self):
        pass
