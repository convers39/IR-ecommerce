from django.test import TestCase, Client
from account.forms import RegisterForm
from account.models import User


class TestAccountForms(TestCase):
    def setUp(self) -> None:
        self.form = RegisterForm
        self.client = Client()

    def test_register_form_data(self):
        data = {
            'username': 'username3',
            'email': 'email3@email.com',
            'password': 'password3',
            'password_confirm': 'password3',
            'agreement': True,
        }
        form = self.form(data)
        self.assertTrue(form.is_valid())

    def test_register_user_POST(self):
        data = {
            'username': 'username3',
            'email': 'email3@email.com',
            'password': 'password3',
            'password_confirm': 'password3',
            'agreement': 'on',
        }
        form = self.form(data)
        res = self.client.post('/account/register/',
                               data=form, content_type='application/x-www-form-urlencoded')
        print('form', res)
        # user = User.objects.get(username='username3')
        # self.assertFalse(user.is_active)
        # TODO: test create user
        self.assertEqual(res.status_code, 200)

    def test_register_form_invalid_username(self):
        data = {
            'username': 'use',
            'email': 'email3email.com',
            'password': 'password3',
            'password_confirm': 'password',
            'agreement': False,
        }
        form = self.form(data)
        print('form error', form.errors)
        self.assertFalse(form.is_valid())
