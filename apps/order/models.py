from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta, timezone

from django_fsm import FSMField, transition
import stripe

from db.base_model import BaseModel
from shop.models import ProductSKU
from account.models import User, Address
from account.tasks import async_send_email
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
        _("payment status"), choices=Status.choices, default=Status.PENDING)
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

    # def check_payment_status(self):
    #     intent = stripe.PaymentIntent.retrieve(self.number)
    #     charges = intent.charges.data  # list or charges

    def is_expired(self):
        """
        check if payment session expired, stripe checkout session will expire after 24hrs
        minimum expired time need to deduct the time interval of expire_payments cron job
        """
        time_elapsed = (datetime.now(timezone.utc) - self.created_at)
        return timedelta(hours=48) > time_elapsed > timedelta(minutes=30, hours=23) and self.status == 'PD'

    def is_auto_canceled(self):
        """
        check if need to cancel payment and all attached orders after 48hrs
        """
        time_elapsed = (datetime.now(timezone.utc) - self.created_at)
        return time_elapsed > timedelta(hours=48) and self.status in ['PD', 'EX']

    @transition(field=status, source='PD', target='SC')
    def pay(self):
        # send email to admin user
        subject = f'Payment {self.number} Received'
        message = f'Payment has been confirmed, please prepare shipment.'
        from_email = settings.EMAIL_FROM
        recipient_list = [settings.EMAIL_HOST_USER, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source='PD', target='EX', conditions=[is_expired])
    def expire_payment(self):
        self.session_id = ''
        self.number = ''

    @transition(field=status, source='EX', target='PD')
    def renew_payment(self, session):
        self.session_id = session.id
        self.number = session.payment_intent
        self.save()

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
        CANCELLING = 'CL', _('Cancelling')
        CANCELLED = 'CX', _('Cancelled')
        SHIPPED = 'SP', _('Shipped')
        RETURNING = 'RT', _('Returning')
        COMPLETED = 'CP', _('Completed')

    number = models.CharField(
        _("order number"), max_length=100, default='', unique=True)
    slug = models.SlugField(_("slug"), null=True)
    status = FSMField(_("order status"),
                      choices=Status.choices, default=Status.NEW)
    subtotal = models.DecimalField(
        _("subtotal"), max_digits=9, decimal_places=0)
    shipping_fee = models.DecimalField(
        _("shipping fee"), max_digits=5, decimal_places=0, default='500')
    return_at = models.DateTimeField(_('return at'), null=True)

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

    def is_refundable(self):
        return self.status == 'CL'

    def in_return_deadline(self):
        # retrieve shipment or deliver day if using a shipment api
        time_elapsed = (datetime.now(timezone.utc) - self.created_at)
        return time_elapsed < timedelta(days=32) and self.status == 'SP'

    def is_completed(self):
        if self.status == 'SP':
            time_elapsed = (datetime.now(timezone.utc) - self.created_at)
            return time_elapsed >= timedelta(days=32)
        elif self.status == 'RT':
            time_elapsed = (datetime.now(timezone.utc) - self.return_at)
            return time_elapsed >= timedelta(days=30)

    @transition(field=status, source='NW', target='CF', conditions=[is_confirmed])
    def confirm(self):
        # send email
        subject = f'Order# {self.number} Confirmed'
        message = f'Hi! {self.user.username}, your order has been confirmed, will be shipped in 48hrs.'
        from_email = settings.EMAIL_FROM
        recipient_list = [self.user.email, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    # shipping needs to be an action function in admin page
    # @transition(field=status, source='CF', target='SP')
    # def deliver(self):
    #     # shipping logic
    #     return True

    @transition(field=status, source='SP', target='RT', conditions=[in_return_deadline])
    def return_product(self):
        self.return_at = datetime.now()
        subject = f'Order# {self.number} Return Request'
        message = f'Return request from customer {self.user.username}'
        from_email = settings.EMAIL_FROM
        recipient_list = [settings.EMAIL_HOST_USER, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source=['NW', 'CF'], target='CL')
    def request_cancel_order(self):
        """
        Only use when customer ask for cancellation, 
        possible to request cancellation from new and confirmed orders,
        send email to admin for cancel operation
        """
        subject = f'Order# {self.number} Cancellation'
        message = f'Cancellation request from customer {self.user.username}'
        from_email = settings.EMAIL_FROM
        recipient_list = [settings.EMAIL_HOST_USER, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source=['NW'], target='CX')
    def auto_cancel(self):
        """
        Cancel order automatically after 48hrs without payment confirmation
        This only use for automatic cancellation in cron jobs, 
        requested cancellation from customer need to be canceled on admin page.
        """
        subject = f'Order# {self.number} Cancellation'
        message = f'Your order has been canceled'
        from_email = settings.EMAIL_FROM
        recipient_list = [self.user.email, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source=['SP', 'RT'], target='CP')
    def complete(self):
        # send email with coupon and asking for review
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
