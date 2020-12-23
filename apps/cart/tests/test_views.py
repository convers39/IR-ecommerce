from django.contrib.messages import get_messages
from django.db.models.signals import post_save
from django.test import TestCase, Client, override_settings, RequestFactory
from django.urls import reverse

import json
import factory
from django_redis import get_redis_connection

from account.models import User
from account.tests.factory import UserFactory, AddressFactory
from shop.tests.factory import SkuFactory, CategoryFactory
from cart.views import CartInfoView, CartAddView, CartUpdateView, CartDeleteView, CheckoutView


class TestCartView(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        # enforce_csrf_checks=True to check csrf token in case

    def tearDown(self):
        get_redis_connection("cart").flushdb()
        get_redis_connection("default").flushdb()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.payload = {'sku_id': '1', 'count': '1'}
        cls.content_type = "application/json"
        cls.user = UserFactory()
        cls.category = CategoryFactory()
        cls.conn = get_redis_connection('cart')
        cls.key = f'cart_{cls.user.id}'
        for _ in range(5):
            dummy = SkuFactory()
            dummy.stock = 10
            dummy.category = cls.category
            dummy.save()

    def test_show_cart_info_view(self):
        self.client.force_login(self.user)
        res = self.client.get(reverse('cart:info'))
        self.client.force_login(self.user)
        with factory.django.mute_signals(post_save):
            for _ in range(3):
                sku = SkuFactory(price=5000)
                self.conn.hset(self.key, sku.id, 2)
        context = res.context
        print(context)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.resolver_match.func.__name__,
                         CartInfoView.as_view().__name__)
        self.assertIn('total_count', context)
        self.assertIn('subtotal', context)
        self.assertIn('products', context)

    def test_add_cart_success(self):
        self.client.force_login(self.user)
        res = self.client.post(reverse('cart:add'),
                               self.payload, content_type=self.content_type)
        res_data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['res'], 1)
        self.assertEqual(res_data['msg'], 'Added to cart')
        self.assertEqual(res_data['cart_count'], 1)
        self.assertEqual(res.resolver_match.func.__name__,
                         CartAddView.as_view().__name__)

    def test_add_cart_understock(self):
        self.client.force_login(self.user)
        payload = {'sku_id': '2', 'count': '100'}
        res = self.client.post(reverse('cart:add'),
                               payload, content_type=self.content_type)
        res_data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Understocked')

    def test_add_item_not_exist(self):
        self.client.force_login(self.user)
        payload = {'sku_id': '666', 'count': '1'}
        res = self.client.post(reverse('cart:add'),
                               payload, content_type=self.content_type)
        res_data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Item does not exist')

    def test_add_lack_of_data(self):
        self.client.force_login(self.user)
        payload = {'count': '1'}
        res = self.client.post(reverse('cart:add'),
                               payload, content_type=self.content_type)
        res_data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Lack of data')

    def test_add_invalid_item_count(self):
        self.client.force_login(self.user)
        payload = {'sku_id': '1', 'count': 'c'}
        res = self.client.post(reverse('cart:add'),
                               payload, content_type=self.content_type)
        res_data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Invalid item count')

    def test_add_item_count_less_than_one(self):
        self.client.force_login(self.user)
        payload = {'sku_id': '1', 'count': '0'}
        res = self.client.post(reverse('cart:add'),
                               payload, content_type=self.content_type)
        res_data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'At least 1 item required')

    def test_update_item(self):
        self.client.force_login(self.user)
        payload = {'sku_id': '3', 'count': '3'}
        self.client.post(reverse('cart:add'),
                         payload, content_type=self.content_type)

        payload_update = {'sku_id': '3', 'count': '2'}
        res = self.client.post(reverse('cart:update'),
                               payload_update, content_type=self.content_type)
        res_data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['res'], 1)
        self.assertEqual(res_data['msg'], 'Cart updated')
        self.assertEqual(res_data['sku_id'], '3')
        self.assertEqual(res_data['count'], '2')
        self.assertEqual(res.resolver_match.func.__name__,
                         CartUpdateView.as_view().__name__)

    def test_delete_cart_item(self):
        self.client.force_login(self.user)
        self.client.post(reverse('cart:add'),
                         self.payload, content_type=self.content_type)
        res = self.client.post(reverse('cart:delete'),
                               self.payload, content_type=self.content_type)
        res_data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['res'], 1)
        self.assertEqual(res_data['msg'], 'Item deleted')
        self.assertEqual(res_data['cart_count'], 0)
        self.assertEqual(res.resolver_match.func.__name__,
                         CartDeleteView.as_view().__name__)


class TestCheckoutView(TestCase):

    def setUp(self) -> None:
        self.client = Client()
        self.client.cookies['uuid'] = '12345'

    def tearDown(self) -> None:
        get_redis_connection('cart').flushdb()
        get_redis_connection('default').flushdb()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse('cart:checkout')
        cls.user = UserFactory()
        cls.address = AddressFactory(user=cls.user)
        cls.conn = get_redis_connection('cart')
        cls.key = f'cart_{cls.user.id}'

    def test_checkout_view_login(self):
        self.client.force_login(self.user)
        with factory.django.mute_signals(post_save):
            for _ in range(3):
                sku = SkuFactory(price=5000)
                self.conn.hset(self.key, sku.id, 2)

        res = self.client.get(self.url)
        context = res.context
        self.assertIn('subtotal', context)
        self.assertEqual(len(context['addrs']), 1)
        self.assertIn('shipping_fee', context)
        self.assertIn('total_count', context)
        self.assertIn('total_price', context)
        self.assertIn('form', context)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'cart/checkout.html')
        self.assertEqual(res.resolver_match.func.__name__,
                         CheckoutView.as_view().__name__)

    # FIXME: cannot set uuid cookie for guest user
    # def test_guest_checkout(self):
    #     with factory.django.mute_signals(post_save):
    #         for _ in range(3):
    #             sku = SkuFactory(price=5000)
    #             self.conn.hset('guest_12345', sku.id, 2)
    #     res = self.client.get(self.url)

    #     self.assertEqual(res.status_code, 200)
    #     self.assertTemplateUsed(res, 'cart/checkout.html')
    #     self.assertEqual(res.resolver_match.func.__name__,
    #                      CheckoutView.as_view().__name__)

    def test_cart_is_empty(self):
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        msg = list(get_messages(res.wsgi_request))

        self.assertRedirects(res, '/cart/', 302, 200)
        self.assertEqual(str(msg[0]), 'Cart is empty')
