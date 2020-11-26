from django.db import models
from db.base_model import BaseModel
from django.utils.translation import ugettext_lazy as _

from django_fsm import FSMField, transition

from shop.models import ProductSKU
from account.models import User, Address


class Payment(BaseModel):

    class Status(models.TextChoices):
        PD = 'PD', _('Pending')
        CF = 'CF', _('Confirmed')
        FL = 'FL', _('Failed')
        EX = 'EX', _('Expired')
        CX = 'CX', _('Canceled')
        RF = 'RF', _('Refunded')

    class Method(models.TextChoices):
        ST = 'ST', _('Stripe')
        PP = 'PP', _('Paypal')

    number = models.CharField(_("payment number"), max_length=50)
    status = FSMField(
        _("payment status"), choices=Status.choices, default='PD')
    amount = models.DecimalField(_("amount"), max_digits=9, decimal_places=0)
    method = models.CharField(
        _("payment method"), choices=Method.choices, max_length=50)
    expired = models.BooleanField(_("is expired"), default=False)

    user = models.ForeignKey("account.user", verbose_name=_(
        "user"), on_delete=models.CASCADE)

    class Meta:
        pass

    def __str__(self):
        return f'Payment {self.number} for {self.user}'

# class Invoice(BaseModel):
#     invoice_no = models.CharField(_("invoice number"), max_length=50)
#     user = models.ForeignKey(
#         "account.user", verbose_name=_(""), on_delete=models.CASCADE)
#     address = models.ForeignKey(
#         "account.address", verbose_name=_(""), on_delete=models.CASCADE)


class Order(BaseModel):

    class Status(models.TextChoices):
        NW = 'NW', _('New')
        MF = 'MF', _('ModifyFreight')
        PP = 'PP', _('PendingPayment')
        CF = 'CF', _('Confirmed')
        CX = 'CX', _('Canceled')
        SP = 'SP', _('Shipped')

    number = models.CharField(_("order number"), max_length=50)
    status = FSMField(_("order status"), choices=Status.choices, default='NW')
    subtotal = models.DecimalField(
        _("subtotal"), max_digits=9, decimal_places=0)
    shipping_fee = models.DecimalField(
        _("shipping fee"), max_digits=5, decimal_places=0)

    payment = models.ForeignKey(
        Payment, verbose_name=_("payment"), on_delete=models.CASCADE)
    user = models.ForeignKey("account.user", verbose_name=_(
        "user"), on_delete=models.CASCADE)
    address = models.ForeignKey("account.address", verbose_name=_(
        "address"), on_delete=models.CASCADE)

    class Meta:
        pass

    def __str__(self):
        return f'Order {self.number} for {self.user}'

    @property
    def total_amount(self):
        return self.subtotal + self.shipping_fee


class OrderProduct(BaseModel):

    unit_price = models.DecimalField(
        _("unit price"), max_digits=9, decimal_places=0)
    count = models.IntegerField(_("count"))
    review = models.TextField(_("review"))

    product = models.ForeignKey(
        "shop.productsku", verbose_name=_("sku"), on_delete=models.CASCADE)
    order = models.ForeignKey(Order, verbose_name=_(
        "order"), on_delete=models.CASCADE)

    def __str__(self):
        return f'Order of {self.product}'
