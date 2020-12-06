from django.test import SimpleTestCase
from django.urls import reverse, resolve

from order.views import CheckoutView, OrderProcessView, PaymentSuccessView, checkout_webhook


class TestOrderUrls(SimpleTestCase):

    def test_cart_info_url(self):
        url = reverse('order:checkout')
        self.assertEqual(url, '/order/checkout/')
        self.assertEqual(resolve(url).func.__name__,
                         CheckoutView.as_view().__name__)

    def test_cart_add_url(self):
        url = reverse('order:process')
        self.assertEqual(url, '/order/process/')
        self.assertEqual(resolve(url).func.__name__,
                         OrderProcessView.as_view().__name__)

    def test_payment_success_url(self):
        url = reverse('order:success')
        self.assertEqual(url, '/order/success/')
        self.assertEqual(resolve(url).func.__name__,
                         PaymentSuccessView.as_view().__name__)

    def test_checkout_webhook_url(self):
        url = reverse('order:webhook')
        self.assertEqual(url, '/order/webhook/')
        self.assertEqual(resolve(url).func.__name__,
                         checkout_webhook.__name__)
