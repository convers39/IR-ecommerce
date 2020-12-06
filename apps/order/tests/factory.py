from datetime import datetime, timedelta, timezone

import factory
from factory.django import DjangoModelFactory

from account.tests.factory import UserFactory, AddressFactory
from shop.tests.factory import SkuFactory
from order.models import Order, Payment, OrderProduct, Review


class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = Payment

    number = ''
    # status = 'PD'
    amount = 6000
    # method = 'CARD'
    session_id = ''
    created_at = factory.LazyFunction(datetime.now)
    user = factory.SubFactory(UserFactory)


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    number = ''
    # status = 'NW'
    subtotal = 5000
    shipping_fee = 1000

    payment = factory.SubFactory(PaymentFactory)
    user = factory.SubFactory(UserFactory)
    address = factory.SubFactory(AddressFactory)

    created_at = factory.LazyFunction(datetime.now)


class OrderProductFactory(DjangoModelFactory):
    class Meta:
        model = OrderProduct

    unit_price = 500
    count = 2
    product = factory.SubFactory(SkuFactory)
    order = factory.SubFactory(OrderFactory)


class ReviewFactory(DjangoModelFactory):
    class Meta:
        model = Review

    star = 5
    comment = factory.Faker('sentence')
    order_product = factory.SubFactory(OrderProductFactory)
