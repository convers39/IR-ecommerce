from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField

from db.base_model import BaseModel

# Create your models here.


class AccountManager(BaseUserManager):

    def create_user(self, user_name, email, password, **other_fields):
        if not user_name:
            raise ValueError(_('A username address is required.'))
        if not email:
            raise ValueError(_('An email address is required.'))
        email = self.normalize_email(email)
        user = self.model(email=email, user_name=user_name, **other_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, user_name, email, password, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_active', True)
        other_fields.setdefault('is_superuser', True)

        if not other_fields.get('is_staff'):
            raise ValueError('Superuser must be assigned to a staff.')

        if not other_fields.get('is_superuser'):
            raise ValueError('Superuser must be assigned to a superuser.')

        return self.create_user(user_name, email, password, **other_fields)


class User(PermissionsMixin, AbstractBaseUser):

    username_validator = UnicodeUsernameValidator()

    user_name = models.CharField(_("user name"), max_length=50, validators=[
        username_validator], help_text=_('Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only.'))
    email = models.EmailField(_("email"), unique=True, max_length=254)
    first_name = models.CharField(_("first name"), max_length=50, blank=True)
    last_name = models.CharField(_("last name"), max_length=50, blank=True)
    phone_no = models.CharField(_("phone no."), max_length=50, blank=True, help_text=(
        'Enter your phone number, cell phone is preferable, e.g. +817088889999'), validators=[RegexValidator(r'^(\+)?[0-9]+')])
    is_staff = models.BooleanField(_("staff"), default=False)
    is_active = models.BooleanField(_("active"), default=False)
    is_superuser = models.BooleanField(_("superuser"), default=False)
    date_joined = models.DateTimeField(
        _("date joined"), default=timezone.now)

    objects = AccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']

    def __str__(self):
        return self.user_name


class AddressManager(models.Manager):
    def get_default_address(self, user):
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            address = None
        return address


class Address(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipient = models.CharField(_("recipient"), max_length=50)
    phone_no = models.CharField(_("phone number"), max_length=50)
    addr = models.CharField(_("address"), max_length=250)
    city = models.CharField(_("city"), max_length=50)
    country = CountryField(_("country"), blank_label='(select country)')
    zip_code = models.CharField(_("zip code"), max_length=20,
                                validators=[RegexValidator(r'^[0-9]+')])
    is_default = models.BooleanField(_("default address"), default=False)

    objects = AddressManager()

    def __str__(self):
        return f'{self.user} (recipient: {self.recipient})'

    class Meta:
        verbose_name_plural = 'addresses'
