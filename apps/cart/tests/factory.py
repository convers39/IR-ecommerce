import factory
from factory.django import DjangoModelFactory

from account.models import User


class UserFacotry(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'awesomeuser %d' % n)
    email = factory.Faker('email')
