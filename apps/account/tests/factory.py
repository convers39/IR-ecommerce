import factory
from factory.django import DjangoModelFactory

from account.models import User, Address


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'awesomeuser %d' % n)
    email = factory.Faker('email')
    last_name = factory.Faker('last_name')
    first_name = factory.Faker('first_name')
    phone_no = '+88 123456789'
    is_active = True


class AddressFactory(DjangoModelFactory):
    class Meta:
        model = Address

    user = factory.SubFactory(UserFactory)
    recipient = factory.Faker('name')
    phone_no = factory.Faker('phone_number')
    addr = factory.Faker('street_address')
    city = factory.Faker('city')
    province = factory.Faker('city')  # do not have province/state provider
    country = factory.Faker('country_code')
    zip_code = factory.Faker('postcode')
    is_default = False
