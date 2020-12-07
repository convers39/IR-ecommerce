from django.test import TestCase, Client
from django.urls.base import reverse
from account.forms import RegisterForm
from account.models import User

from .factory import UserFactory, AddressFactory


class TestAccountForms(TestCase):

    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.form = RegisterForm
        cls.url = reverse('account:register')
        UserFactory(username='username', email='email@email.com',
                    password='password1')

    def test_register_form_data_is_valid(self):
        data = {
            'username': 'username3',
            'email': 'email3@email.com',
            'password': 'password3',
            'password_confirm': 'password3',
            'agreement': True,
        }
        form = self.form(data)
        self.assertTrue(form.is_valid())

    def test_register_form_invalid_username(self):
        data = {
            'username': 'username',
            'email': 'email1@email.com',
            'password': 'password1',
            'password_confirm': 'password1',
            'agreement': True,
        }
        form = RegisterForm(data)
        res = self.client.post(self.url, data=data)
        self.assertFalse(form.is_valid())
        self.assertFormError(
            res, 'form', 'username', 'This username has been used.')

    def test_register_form_invalid_email(self):
        data = {
            'username': 'username2',
            'email': 'email@email.com',
            'password': 'password2',
            'password_confirm': 'password2',
            'agreement': True,
        }
        form = RegisterForm(data)
        res = self.client.post(self.url, data=data)
        self.assertFalse(form.is_valid())
        self.assertFormError(res, 'form', 'email',
                             'This email address is already registered.')

    def test_register_form_invalid_password(self):
        data = {
            'username': 'username2',
            'email': 'email2@email.com',
            'password': 'password3',
            'password_confirm': 'password2',
            'agreement': True,
        }
        form = RegisterForm(data)
        res = self.client.post(self.url, data=data)
        self.assertFalse(form.is_valid())
        self.assertFormError(
            res, 'form', 'password', 'Passwords must match.')
