from django.test import TestCase, Client
from django.test.client import FakePayload
from django.urls import reverse
from django.conf import settings
from django.contrib.messages import get_messages

import time

from itsdangerous import BadData, TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django_redis import get_redis_connection

from account.models import User, Address
from shop.tests.factory import SkuFactory
from order.tests.factory import OrderFactory
from account.views import OrderListView, AddressView, WishlistView
from .factory import UserFactory, AddressFactory


class TestLoginLogoutView(TestCase):
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
        self.activate_url = reverse(
            'account:activate', kwargs={'token': token})

    @classmethod
    def setUpTestData(cls) -> None:
        # urls
        cls.index_url = reverse('shop:index')
        cls.login_url = reverse('account:login')
        cls.logout_url = reverse('account:logout')

    def test_login_GET(self):
        res = self.client.get(self.login_url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'account/login.html')

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


class TestRegisterActivateView(TestCase):
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
        info = {'activate_user': user2.id, 'email': user2.email}
        token = serializer.dumps(info)  # bytes
        token = token.decode()
        self.activate_url = reverse(
            'account:activate', kwargs={'token': token})

    @classmethod
    def setUpTestData(cls) -> None:
        # urls
        cls.index_url = reverse('shop:index')
        cls.login_url = reverse('account:login')
        cls.register_url = reverse('account:register')

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
        url = reverse('account:activate', kwargs={
                      'token': '320di398'})
        res = self.client.get(url)
        msg = list(get_messages(res.wsgi_request))

        self.assertRaises(BadData)
        self.assertEqual(str(msg[0]), 'Invalid request!')
        self.assertRedirects(res, self.index_url, 302, 200)

    def test_register_GET(self):
        res = self.client.get(self.register_url)

        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'account/register.html')

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


class TestAccountCenterView(TestCase):

    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory()
        cls.url = reverse('account:center')
        cls.content_type = 'application/json'
        cls.payload = {
            'username': 'awesome',
            'email': cls.user.email,
            'first_name': cls.user.first_name,
            'last_name': cls.user.last_name,
            'phone_no': cls.user.phone_no
        }

    def test_get_account_info_view_without_login(self):
        res = self.client.get(self.url)
        self.assertRedirects(res, '/account/login/?next=/account/', 302, 200)

    def test_get_account_info_view(self):
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        context = res.context

        self.assertIn('form', context)
        self.assertIn('pw_form', context)
        self.assertIn('recent_products', context)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'account/account.html')

    def test_update_data_success(self):
        payload = self.payload.copy()
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['msg'], 'Data updated')

    def test_update_email_pending_verfify(self):
        new_email = 'new@email.com'
        payload = self.payload.copy()
        payload['email'] = new_email
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res_data['msg'], 'Email address will be updated after your verification')
        self.assertNotEqual(self.user.email, new_email)

    def test_post_invalid_data(self):
        payload = FakePayload()
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['errmsg'], 'Invalid data')

    def test_post_incomplete_data(self):
        payload = {}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res_data['errmsg'], 'Incomplete data')

    def test_post_invalid_form_data(self):
        payload = self.payload.copy()
        payload['username'] = '@!$%'
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res_data['errmsg'], 'Invalid form data')


class TestPasswordResetView(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory()
        cls.user.set_password('nmb123')
        cls.user.save()
        cls.url = reverse('account:password-reset')
        cls.content_type = 'application/json'
        cls.payload = {
            'current': 'nmb123',
            'new': 'n1qjwn23',
            'new_confirm': 'n1qjwn23'
        }

    def test_invalid_post_data(self):
        payload = FakePayload()
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['errmsg'], 'Invalid data')

    def test_change_password_succeed(self):
        payload = self.payload.copy()
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['msg'], 'Password changed')

    def test_password_does_not_match(self):
        payload = self.payload.copy()
        payload['new_confirm'] = '290av3f2'
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['errmsg'], 'Passwords does not match')

    def test_current_password_invalid(self):
        payload = self.payload.copy()
        payload['current'] = '123nmb'
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['errmsg'], 'Current password invalid')

    def test_same_as_current_password(self):
        payload = self.payload.copy()
        payload['new'] = 'nmb123'
        payload['new_confirm'] = 'nmb123'
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['errmsg'], 'Same as current password')


class TestAccountOrderView(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory()
        cls.url = reverse('account:order')
        for _ in range(5):
            cls.order = OrderFactory(user=cls.user)

    def test_order_list_view(self):
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        total_count = int(res.context['paginator'].count)
        context = res.context

        self.assertEqual(res.status_code, 200)
        self.assertIn('stripe_key', context)
        self.assertEqual(total_count, 5)
        self.assertTemplateUsed(res, 'account/order.html')
        self.assertEqual(res.resolver_match.func.__name__,
                         OrderListView.as_view().__name__)


class TestAddressView(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory()
        cls.address = AddressFactory(user=cls.user)
        cls.url = reverse('account:address')
        cls.content_type = 'application/json'
        cls.payload = {
            'recipient': 'Spiderman',
            'phone_no': '+88 7392847',
            'addr': 'a fake address',
            'city': 'fake city',
            'province': 'state',
            'country': 'JP',
            'zip_code': '668989',
        }

    def test_address_view_GET(self):
        self.client.force_login(self.user)
        res = self.client.get(self.url)
        context = res.context

        self.assertEqual(res.status_code, 200)
        self.assertIn('addresses', context)
        self.assertIn('form', context)
        self.assertTemplateUsed(res, 'account/address.html')
        self.assertEqual(res.resolver_match.func.__name__,
                         AddressView.as_view().__name__)

    def test_add_new_address_via_POST(self):
        self.client.force_login(self.user)
        payload = self.payload.copy()
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {
                         'res': '1', 'msg': 'New address added', 'new_id': self.address.id + 1})

    def test_delete_address_via_DELETE(self):
        self.client.force_login(self.user)
        payload = {'addr_id': self.address.id}
        res = self.client.delete(self.url, data=payload,
                                 content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['msg'], 'Address deleted')

    def test_update_address_id_missing_via_PUT(self):
        self.client.force_login(self.user)
        payload = self.payload.copy()
        payload['addr_id'] = self.address.id
        payload['recipient'] = 'Ironman'
        res = self.client.put(self.url, data=payload,
                              content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {
                         'res': '1', 'msg': 'Address updated', 'updated_id': self.address.id})

    def test_update_address_id_missing(self):
        self.client.force_login(self.user)
        payload = self.payload.copy()
        payload['recipient'] = 'Ironman'
        res = self.client.put(self.url, data=payload,
                              content_type=self.content_type)
        res_data = res.json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['errmsg'], 'Address id is missing')


class TestWishlistView(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory()
        cls.url = reverse('account:wishlist')
        cls.content_type = 'application/json'
        cls.conn = get_redis_connection('cart')
        cls.key = f'wish_{cls.user.id}'

    def tearDown(cls) -> None:
        get_redis_connection("cart").flushdb()
        get_redis_connection("default").flushdb()

    def test_wishlist_view_GET(self):
        self.client.force_login(self.user)
        for _ in range(3):
            sku = SkuFactory()
            self.conn.sadd(self.key, sku.id)
        res = self.client.get(self.url)
        context = res.context

        self.assertEqual(res.status_code, 200)
        self.assertEqual(context['products'].count(), 3)
        self.assertTemplateUsed(res, 'account/wishlist.html')
        self.assertEqual(res.resolver_match.func.__name__,
                         WishlistView.as_view().__name__)

    def test_add_to_wishlist_POST(self):
        sku = SkuFactory()
        payload = {'sku_id': sku.id}
        for _ in range(3):
            sku = SkuFactory()
            self.conn.sadd(self.key, sku.id)
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': 1, 'msg': 'Item added to wishlist', 'wish_count': 4})

    def test_remove_from_wishlist_POST(self):
        sku = SkuFactory()
        payload = {'sku_id': sku.id}
        self.conn.sadd(self.key, sku.id)
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': 1, 'msg': 'Item removed from wishlist', 'wish_count': 0})

    def test_item_not_exist_POST(self):
        payload = {'sku_id': 999}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload,
                               content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '0', 'errmsg': 'Item does not exist'})

    def test_invalid_data_POST(self):
        payload = {'sku_id': 2}
        self.client.force_login(self.user)
        res = self.client.post(self.url, data=payload)
        #    content_type=self.content_type)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {'res': '0', 'errmsg': 'Invalid data'})
