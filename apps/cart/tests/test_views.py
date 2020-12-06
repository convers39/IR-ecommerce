from django.test import TestCase, Client, override_settings
from django.urls import resolve, reverse
from django_redis import get_redis_connection

import tempfile
import json
from PIL import Image

from account.tests.factory import UserFacotry
from shop.tests.factory import SkuFactory, CategoryFactory
from cart.views import CartInfoView, CartAddView, CartUpdateView, CartDeleteView


def get_temporary_image(temp_file):
    size = (200, 200)
    color = (255, 0, 0, 0)
    image = Image.new("RGB", size, color)
    image.save(temp_file, 'jpeg')
    return temp_file


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
        cls.user = UserFacotry()
        cls.category = CategoryFactory()
        for _ in range(5):
            dummy = SkuFactory()
            dummy.stock = 10
            temp_file = tempfile.NamedTemporaryFile()
            dummy.category = cls.category
            dummy.cover_img = get_temporary_image(temp_file.name)
            dummy.save()

    def test_show_cart_info_view(self):
        self.client.force_login(self.user)
        res = self.client.get(reverse('cart:info'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.resolver_match.func.__name__,
                         CartInfoView.as_view().__name__)

    def test_cart_info_page_without_login(self):
        res = self.client.get(reverse('cart:info'))
        self.assertRedirects(res, '/account/login/?next=/cart/', 302, 200)

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

    def test_add_log_in_required(self):
        res = self.client.post(reverse('cart:add'),
                               self.payload, content_type=self.content_type)
        res_data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['res'], 0)
        self.assertEqual(res_data['errmsg'], 'Please login')

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
        self.assertEqual(res_data['count'], 2)
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
