from django.core.exceptions import ObjectDoesNotExist
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

    def test_str_representation(self):
        user = UserFactory(username='superman')
        self.assertEqual(str(user), 'superman')

    def test_is_guest_user(self):
        guest = UserFactory(username='guest_12345')
        self.assertFalse(self.user.is_guest)
        self.assertTrue(guest.is_guest)


class UserAddressTests(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserFactory(username='superman')
        cls.address = AddressFactory(user=cls.user, is_default=True)

    def test_str_representation(self):
        address = AddressFactory(user=self.user, recipient='wonderwoman')
        self.assertEqual(str(address), 'superman (recipient: wonderwoman)')

    def test_add_address(self):
<<<<<<< HEAD
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
=======
        count = Address.objects.all().count()
        address = AddressFactory(
            user=self.user,
            is_default=False
        )
        self.assertEqual(address.user, self.user)
        self.assertEqual(count+1, Address.objects.all().count())
        self.assertFalse(address.is_default)

    def test_get_default_address(self):
        user2 = UserFactory()
        AddressFactory(user=user2, is_default=False)
        address1 = Address.objects.get_default_address(self.user)
        address2 = Address.objects.get_default_address(user2)
        self.assertEqual(address1, self.address)
        self.assertIsNone(address2)

    def test_full_address(self):
        address = AddressFactory(
            addr='road',
            city='city',
            province='prov',
            country='JP'
        )
>>>>>>> guestcheckout
        self.assertEqual(
            address.full_address, 'road, city City, prov, JP')

    def test_recipient_with_contact(self):
        address = AddressFactory(
            recipient='batman',
            phone_no='054321909'  # dont try to call this number
        )
        self.assertEqual(
            address.recipient_with_contact,
            'Recipient: batman - Contact: 054321909'
        )

    def test_set_default_address(self):
        new = AddressFactory(user=self.user, is_default=False)
        new.set_default_address(self.user)
        self.address.refresh_from_db()
        self.assertTrue(new.is_default)
        self.assertFalse(self.address.is_default)
