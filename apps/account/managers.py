from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class AccountManager(BaseUserManager):

    def create_user(self, username, email, password, **other_fields):
        if not username:
            raise ValueError(_('A username address is required.'))
        if not email:
            raise ValueError(_('An email address is required.'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **other_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_active', True)
        other_fields.setdefault('is_superuser', True)

        if not other_fields.get('is_staff'):
            raise ValueError('Superuser must be assigned to a staff.')

        if not other_fields.get('is_superuser'):
            raise ValueError('Superuser must be assigned to a superuser.')

        return self.create_user(username, email, password, **other_fields)


class AddressManager(models.Manager):
    def get_default_address(self, user):
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            address = None
        return address
