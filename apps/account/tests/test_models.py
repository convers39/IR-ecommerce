from django.test import TestCase
from django.contrib.auth import get_user_model
from django_countries import countries

from account.models import Address, User
from .factory import UserFactory, AddressFactory


class UserAccountTests(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.model = User
        cls.user = UserFactory()

    def test_create_superuser(self):
        super_user = self.model.objects.create_superuser(
            'superuser', 'superuser@test.com', '123456'
        )
        self.assertEqual(super_user.email, 'superuser@test.com')
        self.assertEqual(super_user.username, 'superuser')
        self.assertEqual(str(super_user), 'superuser')
        self.assertTrue(super_user.is_active)
        self.assertTrue(super_user.is_staff)
        self.assertTrue(super_user.is_superuser)

        with self.assertRaises(ValueError):
            self.model.objects.create_superuser(
                username='superuser',
                email='superuser@test.com',
                password='password',
                is_superuser=False
            )

        with self.assertRaises(ValueError):
            self.model.objects.create_superuser(
                username='superuser',
                email='superuser@test.com',
                password='password',
                is_staff=False
            )

        with self.assertRaises(ValueError):
            self.model.objects.create_superuser(
                username='superuser',
                email='',
                password='password',
                is_superuser=True
            )

    def test_create_user(self):
        user = self.model.objects.create_user(
            'username', 'user@test.com', 'password'
        )
        self.assertEqual(user.email, 'user@test.com')
        self.assertEqual(user.username, 'username')
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active)

        with self.assertRaises(ValueError):
            self.model.objects.create_user(
                'abc', '', 'password'
            )


class UserAddressTests(TestCase):

    def test_add_address(self):
        user = User.objects.create_user(
            'username', 'user@test.com', 'password')
        address = AddressFactory(
            user=user, recipient='recipientname',
            phone_no='55550000',
            addr='room 00, 66 building, xx road, yy district',
            city='Oslo',
            country='NO',
            zip_code='777777',
            is_default=True
        )
        self.assertEqual(address.user, user)
        self.assertEqual(address.recipient, 'recipientname')
        self.assertEqual(address.phone_no, '55550000')
        self.assertEqual(
            address.addr, 'room 00, 66 building, xx road, yy district')
        self.assertEqual(address.city, 'Oslo')
        self.assertEqual(address.country.name, 'Norway')
        self.assertEqual(address.zip_code, '777777')
        self.assertTrue(address.is_default)
