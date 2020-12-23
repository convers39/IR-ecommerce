from core.settings.base import DATABASES
from django import utils
from django.test import TestCase
from datetime import datetime, timezone, timedelta
from django.db.models.signals import post_save
from django.test.utils import override_settings

import factory

from shop.tests.factory import SkuFactory
from order.models import Order, Payment, OrderProduct, Review
from account.tests.factory import UserFactory

from ..utils import generate_order_number
from .factory import OrderFactory, OrderProductFactory, PaymentFactory, ReviewFactory


class TestOrderModel(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.order = OrderFactory()
        cls.skus = []
        with factory.django.mute_signals(post_save):
            for _ in range(5):
                sku = SkuFactory(stock=5, sales=1)
                cls.skus.append(sku)

    def test_str_representation(self):
        order = OrderFactory()
        self.assertEqual(
            str(order), f'Order {order.number} for {order.user}')

    def test_create_number_on_save(self):
        start = datetime.now().strftime('%Y%m%d%H%M')
        generator = generate_order_number()
        new_order = OrderFactory()
        self.assertEqual(new_order.number[:12], start)
        self.assertEqual(len(new_order.number), len(new_order.number))
        self.assertEqual(start, generator[:12])

    def test_total_amount(self):
        self.order.subtotal = 2000
        self.order.shipping_fee = 500
        self.assertEqual(self.order.total_amount, 2500)

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_is_confirmed_and_confirm_payment(self):
        self.assertEqual(self.order.status, 'NW')
        self.assertFalse(self.order.is_confirmed())

        self.order.payment = PaymentFactory(status='SC')
        self.assertTrue(self.order.is_confirmed())

        self.order.confirm()
        self.assertEqual(self.order.status, 'CF')

    def test_is_refundable(self):
        order = OrderFactory(status='CL')
        self.assertTrue(order.is_refundable())
        self.assertFalse(self.order.is_refundable())

    def test_is_completed_and_return_deadline(self):
        created = datetime(2020, 10, 10, tzinfo=timezone.utc)
        order1 = OrderFactory(status='SP')
        order1.created_at = created
        order1.save()
        order2 = OrderFactory(
            status='RT', return_at=datetime.now(tz=timezone.utc))
        order3 = OrderFactory(status='SP')

        self.assertTrue(order1.is_completed())
        self.assertFalse(order1.in_return_deadline())
        self.assertFalse(order2.is_completed())
        self.assertTrue(order3.in_return_deadline())
        self.assertFalse(self.order.is_completed())

    def test_cancel_restore_product_stock(self):
        order = OrderFactory(status='CL')
        sku = self.skus[0]
        op = OrderProductFactory(product=sku)
        op.order = order
        op.save()
        order.confirm_cancel()
        order.restore_product_stock()
        sku.refresh_from_db()
        self.assertEqual(order.status, 'CX')
        self.assertEqual(sku.stock, 6)
        self.assertEqual(sku.sales, 0)


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
        )
        self.review.user = UserFactory(username='awesomeguy')
        self.assertEqual(str(self.review),
                         'review for awesome item by awesomeguy')
