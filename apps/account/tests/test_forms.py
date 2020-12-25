from django.test import TestCase, Client
from django.urls.base import reverse

from .factory import UserFactory, AddressFactory
from account.forms import RegisterForm


class TestRegisterForm(TestCase):

    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.form = RegisterForm
        cls.url = reverse('account:register')
        UserFactory(username='username', email='email@email.com',
                    password='password1')
        cls.payload = {
            'username': 'username3',
            'email': 'email3@email.com',
            'password': 'password3',
            'password_confirm': 'password3',
            'agreement': True,
        }

    def test_register_form_data_is_valid(self):
        data = self.payload.copy()
        form = self.form(data)
        self.assertTrue(form.is_valid())

    def test_register_form_invalid_username(self):
        data = self.payload.copy()
        data['username'] = 'username'
        form = RegisterForm(data)
        res = self.client.post(self.url, data=data)
        self.assertFalse(form.is_valid())
        self.assertFormError(
            res, 'form', 'username', 'This username has been used.')

    def test_register_form_invalid_email(self):
        data = self.payload.copy()
        data['email'] = 'email@email.com'
        form = RegisterForm(data)
        res = self.client.post(self.url, data=data)
        self.assertFalse(form.is_valid())
        self.assertFormError(res, 'form', 'email',
                             'This email address is already registered.')

    def test_register_form_password_mismatch(self):
        data = self.payload.copy()
        data['password'] = 'password1'
        data['password_confirm'] = 'password2'
        form = RegisterForm(data)
        res = self.client.post(self.url, data=data)
        self.assertFalse(form.is_valid())
        self.assertFormError(
            res, 'form', 'password', 'Passwords must match.')
