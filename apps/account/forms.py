from django import forms
from django.forms import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User


class RegisterForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Enter username', 'id': 'username'}), min_length=5)
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Enter email', 'id': 'email'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Enter password', 'id': 'password', 'pattern': '(?=.*\d)(?=.*[a-z]).{6,}', 'title': 'Must contain at least one number and one lowercase letter, and at least 6 or more characters'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Confirm your password', 'id': 'password_confirm', 'pattern': '(?=.*\d)(?=.*[a-z]).{6,}', 'title': 'Passwords must be the same'}))
    agreement = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'class': 'custom-control-input', 'id': 'agreement', 'checked': False}), required=True)
    # errors = forms.CharField(widgets=forms.)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean(self):
        super(RegisterForm, self).clean()
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password_confirm != password:
            self.add_error('password', 'Passwords must match')

    def clean_username(self):
        username = self.cleaned_data.get('username')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            raise forms.ValidationError('User name has been used.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email

        raise forms.ValidationError('This email address is already in use.')


class UserLogInForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Enter email', 'id': 'email'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Enter password', 'id': 'password'}))

    class Meta:
        model = User
        fields = ('email', 'password',)


class UserAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                _("This account is inactive."),
                code='inactive',
            )
