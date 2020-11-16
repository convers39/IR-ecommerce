from django.test import TestCase, Client
from django.urls import resolve, reverse
from django.conf import settings
from django.contrib.messages import get_messages

import time

from itsdangerous import BadData, TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from account.models import User, Address


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
        serializer = Serializer(settings.SECRET_KEY, 2)
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

    def test_login_POST_user_inactivated(self):
        res = self.client.post(
            self.login_url, {'email': 'email2@email.com', 'password': 'password2'})
        msg = list(get_messages(res.wsgi_request))
        self.assertEqual(str(msg[0]), 'Account is not activated.')
        self.assertRedirects(res, self.login_url, 302, 200)

    def test_login_POST_invalid_credentials(self):
        res = self.client.post(
            self.login_url, {'email': 'email1@email.com', 'password': 'password2'})
        msg = list(get_messages(res.wsgi_request))
        self.assertEqual(str(msg[0]), 'Invalid credentials.')
        self.assertRedirects(res, self.login_url, 302, 200)

    def test_login_POST_success(self):
        res = self.client.post(
            self.login_url, {'email': 'email1@email.com', 'password': 'password1'})
        self.assertRedirects(res, self.index_url, 302, 200)

    def test_logout_success(self):
        self.client.login(email='email1@email.com', password='password1')
        res = self.client.get(self.logout_url)
        self.assertRedirects(res, self.index_url, 302, 200)

    def test_logout_without_login(self):
        res = self.client.get(self.logout_url)
        self.assertRedirects(res, self.index_url, 302, 200)

    def test_activate_success(self):
        res = self.client.get(self.activate_url)
        msg = list(get_messages(res.wsgi_request))
        self.assertEqual(str(msg[0]), 'Your account has been activated!')
        self.assertRedirects(res, self.login_url, 302, 200)
        # use for response with a context
        # response = self.client.post('/foo/')
        # messages = list(response.context['messages'])
        # self.assertEqual(len(messages), 1)
        # self.assertEqual(str(messages[0]), 'my message')

    def test_activate_token_expired(self):
        time.sleep(3)
        res = self.client.get(self.activate_url)
        msg = list(get_messages(res.wsgi_request))
        self.assertRaises(SignatureExpired)
        self.assertEqual(str(msg[0]), 'Token expired, please register again!')
        self.assertRedirects(res, self.index_url, 302, 200)

    def test_activate_invalid_request(self):
        url = reverse('account:activate', kwargs={'token': '320di398'})
        res = self.client.get(url)
        msg = list(get_messages(res.wsgi_request))
        self.assertRaises(BadData)
        self.assertEqual(str(msg[0]), 'Invalid request!')
        self.assertRedirects(res, self.index_url, 302, 200)

    def test_register_GET(self):
        res = self.client.get(self.register_url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'register.html')

    def test_register_POST_success(self):
        form_data = {
            'username': 'username3',
            'email': 'email3@email.com',
            'password': 'password3',
            'password_confirm': 'password3',
            'agreement': 'on',
        }
        user_count = User.objects.count()
        res = self.client.post(self.register_url, form_data)
        user3 = User.objects.get(username='username3')
        msg = list(get_messages(res.wsgi_request))
        self.assertFalse(user3.is_active)
        self.assertEqual(User.objects.count(), user_count+1)
        self.assertEqual(
            str(msg[0]), 'Your account has been created! Check your email for activation.')
        self.assertRedirects(res, self.index_url, 302, 200)

    def test_register_POST_failed(self):
        form_data = {
            'username': 'username2',
            'email': 'email2@email.com',
            'password': 'password2',
            'password_confirm': 'password2',
            'agreement': 'on',
        }
        res = self.client.post(self.register_url, form_data)
        self.assertEqual(res.status_code, 200)

    def test_account_center_with_login(self):
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
