from django.test import SimpleTestCase
from django.urls import reverse, resolve

from account.views import AccountCenterView, LoginView, LogoutView, RegisterView, ActivateView


class TestAccountUrls(SimpleTestCase):

    def test_login_url(self):
        url = reverse('account:login')
        self.assertEqual(resolve(url).func.__name__,
                         LoginView.as_view().__name__)

    def test_logout_url(self):
        url = reverse('account:logout')
        self.assertEqual(resolve(url).func.__name__,
                         LogoutView.as_view().__name__)

    def test_register_url(self):
        url = reverse('account:register')
        self.assertEqual(resolve(url).func.__name__,
                         RegisterView.as_view().__name__)

    def test_activate_url(self):
        url = reverse('account:activate', kwargs={'token': 'eanovu83'})
        self.assertEqual(resolve(url).func.__name__,
                         ActivateView.as_view().__name__)

    def test_account_center_url(self):
        url = reverse('account:account_center')
        self.assertEqual(resolve(url).func.__name__,
                         AccountCenterView.as_view().__name__)
