from django import forms
from django.forms import ValidationError
from django_countries.widgets import CountrySelectWidget
from django.utils.translation import gettext_lazy as _
from .models import User, Address


class RegisterForm(forms.ModelForm):
    password_confirm = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Confirm your password', 'id': 'password_confirm', 'pattern': '(?=.*\d)(?=.*[a-z]).{6,}', 'title': 'Passwords must be the same'}))
    agreement = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'class': 'custom-control-input', 'id': 'agreement', 'checked': False}), required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username', 'id': 'username'}),
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter email', 'id': 'email'}),
            'password': forms.PasswordInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter password', 'id': 'password', 'pattern': '(?=.*\d)(?=.*[a-z]).{6,}', 'title': 'Must contain at least one number and one lowercase letter, and 6 or more characters'}),
        }
        # labels = {
        #     'name': _(''),
        # }
        help_texts = {
            'username': _('Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        }
        error_messages = {
            'username': {
                'max_length': _("This writer's name is too long."),
            },
        }

    # TODO: consider to move password validation to the frontend.
    def clean(self):
        super(RegisterForm, self).clean()
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password_confirm != password:
            self.add_error('password', 'Passwords must match.')

    def clean_username(self):
        username = self.cleaned_data.get('username')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            raise forms.ValidationError('This username has been used.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email

        raise forms.ValidationError(
            'This email address is already registered.')


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_no', )
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'username',
                'placeholder': 'Enter your username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'email',
                'placeholder': 'e.g. John@example.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'first_name',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'last_name',
                'placeholder': 'Enter your last name'
            }),
            'phone_no': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'phone_number',
                'placeholder': 'e.g.'
            }),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('recipient', 'phone_no', 'addr',
                  'city', 'country', 'province', 'zip_code')
        widgets = {
            'recipient': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': f'recipient',
                'placeholder': 'Enter the recipient name'
            }),
            'phone_no': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'phone_no',
                'placeholder': 'Recipient phone number, e.g. +8766882244'
            }),
            'addr': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'addr',
                'placeholder': 'Address after city'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'city',
                'placeholder': 'Your city'
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'province',
                'placeholder': 'Province or state'
            }),
            'country': CountrySelectWidget(attrs={
                'class': 'form-control form-control-lg',
                'name': 'country',
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'zip_code',
                'placeholder': 'e.g. 552200'
            }),
        }
