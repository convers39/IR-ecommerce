from django.db import models
from db.base_model import BaseModel
from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta
from django_fsm import FSMField, transition
import stripe

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
        PD = 'PD', _('Pending')  # payment session created, pending payment
        SC = 'SC', _('Succeeded')  # payment accepted
        EX = 'EX', _('Expired')  # payment session expire after 24hrs
        RF = 'RF', _('Refunded')

    class Method(models.TextChoices):
        CARD = 'CARD', _('Credit Card')

    # payment_intent id, create refund
    number = models.CharField(_("payment number"), max_length=100, default='')
    status = FSMField(
        _("payment status"), choices=Status.choices, default=Status.PD, protected=True)
    amount = models.DecimalField(_("amount"), max_digits=9, decimal_places=0)
    method = models.CharField(
        _("payment method"), choices=Method.choices, default=Method.CARD, max_length=10)
    # expired = models.BooleanField(_("is expired"), default=False)
    session_id = models.CharField(
        _("payment session id"), max_length=250, default='')

    user = models.ForeignKey("account.user", verbose_name=_(
        "user"), on_delete=models.CASCADE)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'Payment {self.number} for {self.user}'

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

    @transition(field=status, source='PD', target='EX')
    def expire_payment(self):
        return (datetime.now() - self.created_at) <= timedelta(0)

# class Invoice(BaseModel):
#     invoice_no = models.CharField(_("invoice number"), max_length=50)
#     user = models.ForeignKey(
#         "account.user", verbose_name=_(""), on_delete=models.CASCADE)
#     address = models.ForeignKey(
#         "account.address", verbose_name=_(""), on_delete=models.CASCADE)


class Order(BaseModel):

    class Status(models.TextChoices):
        NW = 'NW', _('New')  # created new order
        CF = 'CF', _('Confirmed')  # payment succeeded -> order confirmed
        CX = 'CX', _('Canceled')  # order canceled -> payment intent clear
        SP = 'SP', _('Shipped')
        RT = 'RT', _('Returned')

    number = models.CharField(
        _("order number"), max_length=100, default='', unique=True)
    status = FSMField(_("order status"),
                      choices=Status.choices, default=Status.NW, protected=True)
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
            timestamp = self.created_at.strftime('%Y%m%d%H%M')
            self.number = timestamp + generate_order_number(self)
        return super(Order, self).save(*args, **kwargs)

    @property
    def total_amount(self):
        return self.subtotal + self.shipping_fee

    @transition(field=status, source='NW', target='CF')
    def confirm_payment(self):
        return self.payment.status == 'SC'

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
    count = models.IntegerField(_("count"))

    product = models.ForeignKey(
        ProductSKU, verbose_name=_("sku"), on_delete=models.CASCADE)
    order = models.ForeignKey(Order, verbose_name=_(
        Order), on_delete=models.CASCADE, related_name='order_products')

    def __str__(self):
        return f'Order of {self.product}'

    @property
    def total_price(self):
        return self.unit_price * self.count


class Review(models.Model):

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
