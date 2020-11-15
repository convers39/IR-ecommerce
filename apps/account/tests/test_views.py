from django.test import TestCase, Client
from django.urls import resolve, reverse
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from account.models import User, Address
from account.views import AccountCenterView, LoginView, LogoutView, RegisterView, ActivateView


class TestAccountViews(TestCase):
    def setUp(self):
        self.client = Client()
        # create 1 active user and 1 inactive user
        user1 = User.objects.create_user(
            'username1', 'email1@email.com', 'password1')
        user1.is_active = True
        user1.save()
        user2 = User.objects.create_user(
            'username2', 'email2@email.com', 'password2')
        user2.save()
        # create token for user 2
        serializer = Serializer(settings.SECRET_KEY, 3600*24)
        info = {'activate_user': user2.id}
        token = serializer.dumps(info)  # bytes
        token = token.decode()
        # urls
        self.index_url = reverse('shop:index')
        self.login_url = reverse('account:login')
        self.logout_url = reverse('account:logout')
        self.register_url = reverse('account:register')
        self.activate_url = reverse(
            'account:activate', kwargs={'token': token})
        self.account_center_url = reverse('account:account_center')

    def test_login_GET(self):
        res = self.client.get(self.login_url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'login.html')

    def test_login_POST_invalid_credentials(self):
        login = self.client.post(self.login_url, follow=True, data={
                                 'email': 'email2@email.com', 'password': 'password2'})
        self.assertRedirects(login, self.login_url, 302, 200)

    def test_login_POST_success(self):
        login = self.client.post(self.login_url, follow=True, data={
                                 'email': 'email1@email.com', 'password': 'password1'})
        self.assertRedirects(login, self.index_url, 302, 200)

    def test_logout_GET(self):
        self.client.login(email='email1@email.com', password='password1')
        res = self.client.get(self.logout_url)
        self.assertRedirects(res, self.index_url, 302, 200)

    def test_logout_without_auth(self):
        res = self.client.get(self.logout_url)

        self.assertRedirects(res, self.index_url, 302, 200)

    def test_activate_GET(self):
        res = self.client.get(self.activate_url)
        redirect_url = reverse('account:login')
        self.assertRedirects(res, redirect_url, 302, 200)

    def test_register_GET(self):
        res = self.client.get(self.register_url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'register.html')

    # def test_register_POST_success(self):
    #     credentials = {
    #         'username': 'username3',
    #         'email': 'email3@email.com',
    #         'password': 'password3',
    #         'password_confirm': 'password3',
    #         'agreement': 'on',
    #     }
    #     res = self.client.post(self.register_url, **credentials, follow=True)
    #     print(res)
    #     user3 = User.objects.get(username='username3')
    #     self.assertFalse(user3.is_active)
        # self.assertRedirects(res, self.index_url, 302, 200)

    def test_account_center_view_GET(self):
        login = self.client.login(
            email='email1@email.com', password='password1')
        res = self.client.get(self.account_center_url)
        self.assertTrue(login)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'account.html')

    def test_account_center_without_login(self):
        res = self.client.get(self.account_center_url)
        redirect_url = self.login_url+'?next='+self.account_center_url
        self.assertRedirects(res, redirect_url, 302, 200)
