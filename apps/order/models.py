from django.db import models
from django.shortcuts import reverse
from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta, timezone

from django_fsm import FSMField, transition
import stripe

from db.base_model import BaseModel
from shop.models import ProductSKU
from account.models import User, Address
from .utils import generate_order_number


class Payment(BaseModel):
    """
    This payment model relies on Stripe Checkout service, 
    contains number field to save the paymentIntent object id,
    session_id to save the checkout Session id, which will be useful 
    to retrieve payment session from user account center
    """
    class Status(models.TextChoices):
        # payment session created, pending payment
        PENDING = 'PD', _('Pending')
        SUCCEEDED = 'SC', _('Succeeded')  # payment accepted
        EXPIRED = 'EX', _('Expired')  # payment session expire after 24hrs
        REFUNDED = 'RF', _('Refunded')

    class Method(models.TextChoices):
        CARD = 'CARD', _('Credit Card')

    # payment_intent id, create refund
    number = models.CharField(_("payment number"), max_length=100, default='')
    status = FSMField(
        _("payment status"), choices=Status.choices, default=Status.PENDING, protected=True)
    amount = models.DecimalField(_("amount"), max_digits=9, decimal_places=0)
    method = models.CharField(
        _("payment method"), choices=Method.choices, default=Method.CARD, max_length=10)
    session_id = models.CharField(
        _("payment session id"), max_length=250, default='')

    user = models.ForeignKey("account.user", verbose_name=_(
        "user"), on_delete=models.CASCADE, related_name='payments')

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Payment {self.number} for {self.user}'

    def is_expired(self):
        return (datetime.now(timezone.utc) - self.created_at) > timedelta(hours=24)

    @transition(field=status, source='PD', target='SC')
    def pay(self):
        return True

    @transition(field=status, source='SC', target='RF')
    def create_refund(self):
        # check refund amount

        refund = stripe.Refund.create(payment_intent=self.number)
        # send email to costumer

        # create a cancellation record

        return True

    @transition(field=status, source='PD', target='EX', conditions=[is_expired])
    def expire_payment(self):
        return True

# class Invoice(BaseModel):
#     invoice_no = models.CharField(_("invoice number"), max_length=50)
#     user = models.ForeignKey(
#         "account.user", verbose_name=_(""), on_delete=models.CASCADE)
#     address = models.ForeignKey(
#         "account.address", verbose_name=_(""), on_delete=models.CASCADE)


class Order(BaseModel):

    class Status(models.TextChoices):
        NEW = 'NW', _('New')  # created new order
        # payment succeeded -> order confirmed
        CONFIRMED = 'CF', _('Confirmed')
        # order canceled -> payment cancel
        CANCELED = 'CX', _('Canceled')
        SHIPPED = 'SP', _('Shipped')
        RETURNED = 'RT', _('Returned')

    number = models.CharField(
        _("order number"), max_length=100, default='', unique=True)
    slug = models.SlugField(_("slug"), null=True)
    status = FSMField(_("order status"),
                      choices=Status.choices, default=Status.NEW, protected=True)
    subtotal = models.DecimalField(
        _("subtotal"), max_digits=9, decimal_places=0)
    shipping_fee = models.DecimalField(
        _("shipping fee"), max_digits=5, decimal_places=0, default='500')

    payment = models.ForeignKey(Payment, verbose_name=_(
        "payment"), on_delete=models.SET_NULL, null=True, related_name='orders')
    user = models.ForeignKey(User, verbose_name=_(
        "user"), on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, verbose_name=_(
        "address"), on_delete=models.SET_NULL, null=True, related_name='orders')

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Order {self.number} for {self.user}'

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = generate_order_number()
            self.slug = self.number
        return super(Order, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("account:order-detail", kwargs={"number": self.number})

    @property
    def total_amount(self):
        return self.subtotal + self.shipping_fee

    def is_confirmed(self):
        return self.payment.status == 'SC'

    @transition(field=status, source='NW', target='CF', conditions=[is_confirmed])
    def confirm_payment(self):
        # send email
        return True

    @transition(field=status, source='CF', target='SP')
    def deliver(self):
        # shipping logic
        return True

    @transition(field=status, source=['NW', 'CF'], target='CX')
    def cancel(self):
        # cancel logic
        return True


class OrderProduct(BaseModel):

    unit_price = models.DecimalField(
        _("unit price"), max_digits=9, decimal_places=0)
    count = models.PositiveIntegerField(_("count"))

    product = models.ForeignKey(
        ProductSKU, verbose_name=_("sku"), on_delete=models.CASCADE, related_name='order_products')
    order = models.ForeignKey(Order, verbose_name=_(
        'Order'), on_delete=models.SET_NULL, null=True, related_name='order_products')

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Order of {self.product}'

    @property
    def total_price(self):
        return self.unit_price * self.count

    @property
    def is_reviewed(self):
        return hasattr(self, 'review')


class Review(BaseModel):

    class Star(models.IntegerChoices):
        VS = 5, _('Very satisfied')
        ST = 4, _('Satisfied')
        NT = 3, _('Neutral')
        US = 2, _('Unsatisfied')
        VN = 1, _('Very unsatisfied')

    star = models.PositiveSmallIntegerField(
        _("stars"), choices=Star.choices, default=5)
    comment = models.TextField(_("comment"))

    order_product = models.OneToOneField(
        OrderProduct, verbose_name=_("order product"), on_delete=models.CASCADE, related_name='review')

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'review for {self.order_product.product} by {self.order_product.order.user}'
