from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_countries.fields import CountryField

from db.base_model import BaseModel

from .managers import AccountManager, AddressManager


class User(PermissionsMixin, AbstractBaseUser):

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(_("user name"), max_length=50, validators=[
        username_validator], help_text=_('Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only.'))
    email = models.EmailField(_("email"),  max_length=254, unique=True)
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
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class Address(BaseModel):
    recipient = models.CharField(_("recipient"), max_length=50)
    phone_no = models.CharField(_("phone number"), max_length=50)
    addr = models.CharField(_("address"), max_length=250)
    city = models.CharField(_("city"), max_length=50)
    province = models.CharField(_("state/province"), max_length=50)
    country = CountryField(_("country"), blank_label='(select country)')
    zip_code = models.CharField(_("zip code"), max_length=20,
                                validators=[RegexValidator(r'^[0-9]+')])
    is_default = models.BooleanField(_("default address"), default=False)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='addresses', null=True)

    objects = AddressManager()

    def __str__(self):
        return f'{self.user} (recipient: {self.recipient})'

    class Meta:
        verbose_name_plural = 'addresses'

    @property
    def recipient_with_contact(self):
        return f'Recipient: {self.recipient} -- Contact: {self.phone_no}'

    @property
    def full_address(self):
        return f'{self.addr}, {self.city} City, {self.province}, {self.country}'

    def set_default_address(self, user):
        if not self.is_default:
            current = Address.objects.get_default_address(user)
            current.is_default = False
            current.save()
            self.is_default = True
            self.save()
