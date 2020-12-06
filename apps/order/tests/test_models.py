from django.test import TestCase
from datetime import datetime, timezone, timedelta
from django.db.models.signals import post_save

import factory

from shop.tests.factory import SkuFactory
from order.models import Order, Payment, OrderProduct, Review
from account.tests.factory import UserFactory

from .factory import OrderFactory, OrderProductFactory, PaymentFactory, ReviewFactory


class TestOrderModel(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.order = OrderFactory()
        skus = []
        with factory.django.mute_signals(post_save):
            for _ in range(5):
                sku = SkuFactory()
                skus.append(sku)

    def test_create_order(self):
        count = Order.objects.count()
        new_order = OrderFactory()
        self.assertIsInstance(new_order, Order)
        self.assertEqual(count+1, Order.objects.count())

    def test_str_representation(self):
        self.assertEqual(
            str(self.order), f'Order {self.order.number} for {self.order.user}')

    def test_get_absolute_url(self):
        url = self.order.get_absolute_url()
        # self.order.number = '12345'
        self.assertEqual(url, f'/account/order/{self.order.slug}/')

    def test_create_number_and_slug_on_save(self):
        start = datetime.now().strftime('%Y%m%d%H%M')
        new_order = OrderFactory()
        self.assertEqual(new_order.number[:12], start)
        self.assertEqual(new_order.number, new_order.slug)

    def test_total_amount(self):
        self.order.subtotal = 2000
        self.order.shipping_fee = 500
        self.assertEqual(self.order.total_amount, 2500)

    def test_is_confirmed_and_confirm_payment(self):
        self.assertEqual(self.order.status, 'NW')
        self.assertFalse(self.order.is_confirmed())

        self.order.payment = PaymentFactory(status='SC')
        self.assertTrue(self.order.is_confirmed())

        self.order.confirm_payment()
        self.assertEqual(self.order.status, 'CF')


class TestPaymentModel(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.payment = PaymentFactory()

    def test_create_payment(self):
        count = Payment.objects.count()
        new_payment = PaymentFactory()
        self.assertIsInstance(new_payment, Payment)
        self.assertEqual(count+1, Payment.objects.count())

    def test_str_representation(self):
        self.payment.user.username = 'awesomeguy'
        self.payment.number = '66666'
        self.assertEqual(str(self.payment), 'Payment 66666 for awesomeguy')

    def test_is_expired_and_expire_payment(self):
        self.assertEqual(self.payment.status, 'PD')
        self.assertFalse(self.payment.is_expired())

        self.payment.created_at = datetime.now(
            tz=timezone.utc) - timedelta(hours=24, minutes=1)
        self.assertTrue(self.payment.is_expired())

        self.payment.expire_payment()
        self.assertEqual(self.payment.status, 'EX')

    def test_pay_transition(self):
        new_payment = PaymentFactory()
        self.assertEqual(new_payment.status, 'PD')
        new_payment.pay()
        self.assertEqual(new_payment.status, 'SC')


class TestOrderProductModel(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.order_product = OrderProductFactory()

    def test_create_order_product(self):
        count = OrderProduct.objects.count()
        new_ob = OrderProductFactory()
        self.assertIsInstance(new_ob, OrderProduct)
        self.assertEqual(count+1, OrderProduct.objects.count())

    def test_str_representation(self):
        self.order_product.product.name = 'awesome product'
        self.assertEqual(str(self.order_product), 'Order of awesome product')

    def test_total_price(self):
        self.order_product.unit_price = 500
        self.order_product.count = 3
        self.assertEqual(self.order_product.total_price, 1500)

    def test_is_reviewed(self):
        self.order_product.review = ReviewFactory()
        # comment=
        self.assertTrue(self.order_product.is_reviewed)


class TestReviewModel(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.review = ReviewFactory(
            star=4, comment='awesome item awesome website')

    def test_create_review(self):
        count = Review.objects.count()
        new_review = ReviewFactory()
        self.assertIsInstance(new_review, Review)
        self.assertEqual(count+1, Review.objects.count())

    def test_str_representation(self):
        self.review.order_product = OrderProductFactory(
            product=SkuFactory(name='awesome item'),
            order=OrderFactory(user=UserFactory(username='awesomeguy'))
        )
        self.assertEqual(str(self.review),
                         'review for awesome item by awesomeguy')
