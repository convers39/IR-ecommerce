from django import forms
from django.utils.translation import gettext_lazy as _
# from django.forms import ValidationError, modelformset_factory

from django_countries.widgets import CountrySelectWidget
from django_countries.fields import CountryField
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox

from .models import User, Address


class RegisterForm(forms.ModelForm):
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm your password',
        'id': 'password_confirm',
        'pattern': '(?=.*\d)(?=.*[a-z]).{6,}',
        'title': _('Passwords must be the same')
    }))
    agreement = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'custom-control-input',
        'id': 'agreement',
        'checked': False
    }))
    # captcha = ReCaptchaField(
    #     widget=ReCaptchaV2Checkbox(
    #         attrs={
    #             'class': 'form-control',
    #             'data-theme': 'dark',
    #             'data-size': 'compact',
    #         }
    #     )
    # )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter username'),
                'id': 'username'
            }),
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': _('Enter email'), 'id': 'email'}),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter password'),
                'id': 'password',
                'pattern': '(?=.*\d)(?=.*[a-z]).{6,20}',
                'title': _('Must contain at least one number and one lowercase letter, and 6 to 20 characters')}),
        }

    # TODO: consider to move password validation to the frontend.
    def clean(self):
        super(RegisterForm, self).clean()
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password_confirm != password:
            error = forms.ValidationError(
                _('Passwords must match.'), code='pw_mismatch')
            self.add_error('password', error)

    def clean_username(self):
        username = self.cleaned_data.get('username')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            raise forms.ValidationError(
                _('This username has been used.'), code='username_used')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email

        # NOTE: avoid unique restriction on email
        # for guest user who register an account
        if user.is_guest:
            user.email = user._guest_prefix + email
            user.save()
            return email
        else:
            raise forms.ValidationError(_(
                'This email address is already registered.'), code='email_used')


class UserInfoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super(UserInfoForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_no', )
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'username',
                'pattern': '^[a-zA-Z][a-zA-Z0-9-_\.]{1,30}$',
                'title': _('Enter a valid username in 30 characters. This value may contain only letters,\
                     numbers, and ./-/_ characters.'),
                'placeholder': _('Enter your username')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'email',
                'title': _('Enter a valid email address.'),
                'placeholder': _('e.g. John@example.com')
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'first_name',
                'pattern': '^[A-Za-z]{1,20}$',
                'title': _('Enter a valid first name in 20 characters. This value may contain only letters'),
                'placeholder': _('Enter your first name')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'last_name',
                'pattern': '^[a-zA-Z].{1,20}$',
                'title': _('Enter a valid last name in 20 characters. This value may contain only letters'),
                'placeholder': _('Enter your last name')
            }),
            'phone_no': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'id': 'phone_no',
                'pattern': '^(\+?)[0-9].{6,20}$',
                'title': _('Enter a valid phone number. It can start with country number with +. hyphen or period is not allowed.'),
                'placeholder': _('e.g. +82 66778899')
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email

        if user == self.request_user:
            return email

        raise forms.ValidationError(_(
            'This email address is already registered.'), code='email_used')

    def clean_username(self):
        username = self.cleaned_data.get('username')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user and user != self.request_user:
            raise forms.ValidationError(
                _('This username has been used.'), code='username_used')
        return username


class PasswordResetForm(forms.Form):
    current = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your current password',
        'id': 'currentPassword',
        'pattern': '(?=.*\d)(?=.*[a-z]).{6,20}',
        'title': _('Must contain at least one number and one lowercase letter, and 6 to 20 characters')
    }))
    new = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your new password',
        'id': 'newPassword',
        'pattern': '(?=.*\d)(?=.*[a-z]).{6,20}',
        'title': _('Must contain at least one number and one lowercase letter, and 6 to 20 characters')
    }))
    new_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm your new password',
        'id': 'confirmNewPassword',
        'pattern': '(?=.*\d)(?=.*[a-z]).{6,20}',
        'title': _('Passwords must be the same')
    }))


class ContryForm(forms.Form):
    country = CountryField().formfield()


class GuestAddressForm(forms.Form):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'name': 'first_name',
        'id': 'first_name',
        'pattern': '^[A-Za-z]{1,20}$',
        'title': _('Enter a valid first name in 20 characters. This value may contain only letters'),
        'placeholder': _('e.g. John')
    }))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'name': 'last_name',
        'id': 'last_name',
        'pattern': '^[A-Za-z]{1,20}$',
        'title': _('Enter a valid last name in 20 characters. This value may contain only letters'),
        'placeholder': _('e.g. Doe')
    }))
    phone_no = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'name': 'phone_no',
        'id': 'phone_no',
        'pattern': '^(\+?)[0-9].{6,20}$',
        'title': _('Enter a valid phone number. It can start with country number with +. hyphen or period is not allowed.'),
        'placeholder': _('e.g. +82 66778899')
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control form-control-lg',
        'name': 'email',
        'id': 'email',
        'placeholder': _('Enter your email address')
    }))
    addr = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'name': 'addr',
        'id': 'addr',
        'pattern': '^[a-zA-Z0-9!@#&*(),.|<>].{5,200}$',
        'title': _('Address must be Alpha-Numeric characters and symbols \
            including !@#&*(),.|<>, more than 5 less than 200 characters.'),
        'placeholder': _('Address after city')
    }))
    city = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'name': 'city',
        'id': 'city',
        'pattern': '^[A-Za-z]{1,50}$',
        'title': _('City must be Alphabet and no more than 50 characters.'),
        'placeholder': _('Town or city')
    }))
    province = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'name': 'province',
        'id': 'province',
        'pattern': '^[A-Za-z]{1,50}$',
        'title': _('Province or state must be Alphabet and no more than 50 characters.'),
        'placeholder': _('State or province')
    }))
    country = CountryField(blank_label='(Select country)').\
        formfield(widget=CountrySelectWidget(attrs={
            'class': 'form-control form-control-lg',
            'name': 'country',
            'id': 'country',
        }, layout='{widget}'))
    zip_code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'name': 'zip_code',
        'id': 'zip_code',
        'pattern': '^[A-Za-z0-9].{4,30}$',
        'title': _('Postal code must be Alpha-Numeric and no more than 30 characters.'),
        'placeholder': _('e.g. 555000')
    }))
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(
            attrs={
                'class': 'form-control',
                'data-theme': 'dark',
                'data-size': 'compact',
            }
        )
    )


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('recipient', 'phone_no', 'addr',
                  'city', 'country', 'province', 'zip_code')
        widgets = {
            'recipient': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': f'recipient',
                'pattern': '^[A-Za-z]{1,20}$',
                'title': _('Enter a recipient name in 20 characters. This value may contain only letters'),
                'placeholder': _('Enter the recipient name')
            }),
            'phone_no': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'phone_no',
                'pattern': '^(\+?)[0-9].{6,20}$',
                'title': _('Enter a valid phone number. It can start with country number with +. hyphen or period is not allowed.'),
                'placeholder': _('Recipient phone number, e.g. +8766882244')
            }),
            'addr': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'addr',
                'pattern': '^[a-zA-Z0-9!@#&*(),.|<>].{5,200}$',
                'title': _('Address must be Alpha-Numeric characters and symbols \
                    including !@#&*(),.|<>, more than 5 less than 200 characters.'),
                'placeholder': _('Address after city')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'city',
                'pattern': '^[A-Za-z]{1,50}$',
                'title': _('City must be Alphabet and no more than 50 characters.'),
                'placeholder': _('Your city')
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'province',
                'pattern': '^[A-Za-z]{1,50}$',
                'title': _('Province or state must be Alphabet and no more than 50 characters.'),
                'placeholder': _('Province or state')
            }),
            'country': CountrySelectWidget(attrs={
                'class': 'form-control form-control-lg',
                'name': 'country',
            }, layout='{widget}'),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'name': 'zip_code',
                'pattern': '^[A-Za-z0-9].{4,30}$',
                'title': _('Postal code must be Alpha-Numeric and no more than 30 characters.'),
                'placeholder': _('e.g. 552200')
            }),
        }


# def create_address_formset(user):
#     AddressFormSet = modelformset_factory(Address, form=AddressForm)
#     formset = AddressFormSet(queryset=Address.objects.filter(user=user))
#     return formset
