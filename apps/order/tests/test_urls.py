from django.test import SimpleTestCase
from django.urls import reverse, resolve

from order.views import(OrderProcessView, PaymentSuccessView, PaymentRenewView,
                        checkout_webhook, OrderCancelView, OrderSearchView, OrderCommentView)


class TestOrderUrls(SimpleTestCase):

    def test_order_search_url(self):
        url = reverse('order:search')
        self.assertEqual(url, '/order/search/')
        self.assertEqual(resolve(url).func.__name__,
                         OrderSearchView.as_view().__name__)

    def test_order_process_url(self):
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

    def test_payment_success_url(self):
        url = reverse('order:success')
        self.assertEqual(url, '/order/success/')
        self.assertEqual(resolve(url).func.__name__,
                         PaymentSuccessView.as_view().__name__)

    def test_payment_renew_url(self):
        url = reverse('order:payment-renew')
        self.assertEqual(url, '/order/paymentrenew/')
        self.assertEqual(resolve(url).func.__name__,
                         PaymentRenewView.as_view().__name__)

    def test_order_cancel_url(self):
        url = reverse('order:cancel')
        self.assertEqual(url, '/order/cancel/')
        self.assertEqual(resolve(url).func.__name__,
                         OrderCancelView.as_view().__name__)

    def test_order_comment_url(self):
        url = reverse('order:comment')
        self.assertEqual(url, '/order/comment/')
        self.assertEqual(resolve(url).func.__name__,
                         OrderCommentView.as_view().__name__)
