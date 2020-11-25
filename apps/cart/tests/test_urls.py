from django.test import SimpleTestCase
from django.urls import reverse, resolve

from cart.views import CartInfoView, CartAddView, CartUpdateView, CartDeleteView


class TestCartUrls(SimpleTestCase):

    def test_cart_info_url(self):
        url = reverse('cart:info')
        self.assertEqual(url, '/cart/')
        self.assertEqual(resolve(url).func.__name__,
                         CartInfoView.as_view().__name__)

    def test_cart_add_url(self):
        url = reverse('cart:add')
        self.assertEqual(url, '/cart/add/')
        self.assertEqual(resolve(url).func.__name__,
                         CartAddView.as_view().__name__)

    def test_cart_update_url(self):
        url = reverse('cart:update')
        self.assertEqual(url, '/cart/update/')
        self.assertEqual(resolve(url).func.__name__,
                         CartUpdateView.as_view().__name__)

    def test_cart_delete_url(self):
        url = reverse('cart:delete')
        self.assertEqual(url, '/cart/delete/')
        self.assertEqual(resolve(url).func.__name__,
                         CartDeleteView.as_view().__name__)
