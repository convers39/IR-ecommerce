from django.test import SimpleTestCase
from django.urls import reverse, resolve

from account.views import (LoginView, LogoutView, RegisterView, ActivateView, PasswordResetView,
                           AccountCenterView, OrderListView,  AddressView, WishlistView)


class TestAccountUrls(SimpleTestCase):

    def test_login_url(self):
        url = reverse('account:login')
        self.assertEqual(url, '/account/login/')
        self.assertEqual(resolve(url).func.__name__,
                         LoginView.as_view().__name__)

    def test_logout_url(self):
        url = reverse('account:logout')
        self.assertEqual(url, '/account/logout/')
        self.assertEqual(resolve(url).func.__name__,
                         LogoutView.as_view().__name__)

    def test_register_url(self):
        url = reverse('account:register')
        self.assertEqual(url, '/account/register/')
        self.assertEqual(resolve(url).func.__name__,
                         RegisterView.as_view().__name__)

    def test_activate_url(self):
        url = reverse('account:activate', kwargs={'token': 'eanovu83'})
        self.assertEqual(url, '/account/activate/eanovu83/')
        self.assertEqual(resolve(url).func.__name__,
                         ActivateView.as_view().__name__)

    def test_account_center_url(self):
        url = reverse('account:center')
        self.assertEqual(url, '/account/')
        self.assertEqual(resolve(url).func.__name__,
                         AccountCenterView.as_view().__name__)

    def test_account_address_url(self):
        url = reverse('account:address')
        self.assertEqual(url, '/account/address/')
        self.assertEqual(resolve(url).func.__name__,
                         AddressView.as_view().__name__)

    def test_account_order_url(self):
        url = reverse('account:order')
        self.assertEqual(url, '/account/order/')
        self.assertEqual(resolve(url).func.__name__,
                         OrderListView.as_view().__name__)

    def test_account_wishlist_url(self):
        url = reverse('account:wishlist')
        self.assertEqual(url, '/account/wishlist/')
        self.assertEqual(resolve(url).func.__name__,
                         WishlistView.as_view().__name__)

    def test_password_reset_url(self):
        url = reverse('account:password-reset')
        self.assertEqual(url, '/account/passwordreset/')
        self.assertEqual(resolve(url).func.__name__,
                         PasswordResetView.as_view().__name__)
