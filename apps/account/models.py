from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.


class AccountManager(BaseUserManager):
    """[summary]

    Args:
        BaseUserManager ([type]): [description]
    """

    def create_user(self, user_name, email, password, **other_fields):
        """
        docstring
        """
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
        """
        docstring
        """
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_active', True)
        other_fields.setdefault('is_superuser', True)

        if not other_fields.get('is_staff'):
            raise ValueError('Superuser must be assigned to a staff.')

        if not other_fields.get('is_superuser'):
            raise ValueError('Superuser must be assigned to a superuser.')

        return self.create_user(user_name, email, password, **other_fields)


class User(PermissionsMixin, AbstractBaseUser):
    """[summary]

    Args:
        PermissionsMixin ([type]): [description]
        AbstractBaseUser ([type]): [description]
    """
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
