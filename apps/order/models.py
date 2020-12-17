from django.core.checks.messages import Error
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.shortcuts import reverse
from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta, timezone

from django_fsm import FSMField, transition, GET_STATE, RETURN_VALUE
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
        ALIPAY = 'ALIPAY', _('Alipay')
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

    @transition(field=status, source='EX', target='PD')
    def refund(self, amount=None):
        refund = stripe.Refund.create(
            amount=amount, payment_intent=self.number)
        if refund.status == 'succeeded':
            subject = f'Payment {self.number} Refunded'
            message = f'Payment has been refunded, this will take few days to refund to your account or card.'
            from_email = settings.EMAIL_FROM
            recipient_list = [self.user.email, ]
            async_send_email.delay(
                subject, message, from_email, recipient_list)
        else:
            raise Exception(
                f'Failed to create a refund instance, status: {refund.status}')

# class Invoice(BaseModel):
#     invoice_no = models.CharField(_("invoice number"), max_length=50)
#     user = models.ForeignKey(
#         "account.user", verbose_name=_(""), on_delete=models.CASCADE)
#     address = models.ForeignKey(
#         "account.address", verbose_name=_(""), on_delete=models.CASCADE)

# TODO: save refund record when apply a refund
# class RefundRecord(BaseModel):
#     number = models.CharField(_("refund id"), max_length=100, default='')
#     amount = models.DecimalField(
#         _("refund amount"), max_digits=9, decimal_places=0)

#     payment = models.OneToOneField(Payment, verbose_name=_(
#         "payment"), on_delete=models.CASCADE, related_name='refunds')


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
                      choices=Status.choices, default=Status.NEW, protected=True)
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

    def restore_product_stock(self):
        """
        Use to restore product stock and sales data after cancellation
        """
        if self.status == 'CX':
            products = [
                op.product for op in self.order_products.select_related('product')]
            for product in products:
                product.sales = F('sales') - 1
                product.stock = F('stock') + 1
            ProductSKU.objects.bulk_update(products, ['sales', 'stock'])
        else:
            raise Exception(
                'This method can only be applied to cancelled orders')

    @transition(field=status, source='NW', target='CF', conditions=[is_confirmed])
    def confirm(self):
        subject = f'Order# {self.number} Confirmed'
        message = f'Hi! {self.user.username}, your order has been confirmed, will be shipped in 48hrs.'
        from_email = settings.EMAIL_FROM
        recipient_list = [self.user.email, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source='CF', target='SP')
    def ship(self):
        """
        This method is only called in admin page to ship a order.
        TODO: add permissions to admin only methods
        """
        subject = f'Order# {self.number} Shipping'
        message = f'Your order has been shipped, tracking number is xxx'
        from_email = settings.EMAIL_FROM
        recipient_list = [self.user.email, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source='SP', target='RT', conditions=[in_return_deadline])
    def request_return(self):
        """
        User can request to return products within deadline, send an email to admin for further operation.
        """
        self.return_at = datetime.now()
        subject = f'Order# {self.number} Return Request'
        message = f'Return request from customer {self.user.username}'
        from_email = settings.EMAIL_FROM
        recipient_list = [settings.EMAIL_HOST_USER, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source=['NW', 'CF'], target='CL')
    def request_cancel(self):
        # TODO: add frontend logic and cancelation view
        """
        Only use when customer ask for cancellation, 
        possible to request cancellation from new and confirmed orders,
        send email to admin for cancel operation
        """
        subject = f'Order# {self.number} Cancellation Request'
        message = f'Cancellation request from customer {self.user.username}'
        from_email = settings.EMAIL_FROM
        recipient_list = [settings.EMAIL_HOST_USER, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source=['CL'], target=RETURN_VALUE('CF', 'NW'))
    def stop_cancel_request(self):
        """
        Use by a customer or an admin to stop a cancellation request and move back to the former state.
        """
        return 'CF' if self.is_confirmed() else 'NW'

    @transition(field=status, source=['RT'], target='SP')
    def stop_return_request(self):
        """
        Use by a customer or an admin to stop a return request and move back to shipped state,
        if order is over the return deadline, it will be handled by cron job.
        """
        return True

    @transition(field=status, source=['NW'], target='CX')
    def auto_cancel(self):
        """
        Cancel order automatically after 48hrs without payment confirmation
        This method is used for automatic cancellation in cron jobs, 
        also for NEW orders before payment confirmed, which does not require admin operations.
        """
        subject = f'Order# {self.number} Cancellation'
        message = f'Your order has been canceled due to the expiration of payment'
        from_email = settings.EMAIL_FROM
        recipient_list = [self.user.email, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source=['CL'], target='CX')
    def comfirm_cancel(self):
        """
        This method will only be called in the admin page to confirm a cancellation request from the customer
        """
        subject = f'Order# {self.number} Cancellation'
        message = f'Your order has been canceled'
        from_email = settings.EMAIL_FROM
        recipient_list = [self.user.email, ]
        async_send_email.delay(subject, message, from_email, recipient_list)

    @transition(field=status, source=['SP', 'RT'], target='CP')
    def complete(self):
        """
        This method is used in cron job or manully operated by an admin.
        """
        # send email with coupon and asking for review
        subject = f'Order# {self.number} Cancellation'
        message = f'Your order is completed, please tell us your thoughts.\
            \nWrite a review: link\nContact us'
        from_email = settings.EMAIL_FROM
        recipient_list = [self.user.email, ]
        async_send_email.delay(subject, message, from_email, recipient_list)


#  TODO: create cancel record when a cancel/refund request is launched
# class CancelRecord(BaseModel):
#     class Executor(models.TextChoices):
#         # requested by customer (confirmed by admin)
#         CUSTOMER = 'CM', _('Customer')
#         ADMIN = 'AD', _('Admin')  # canceled by admin
#         # cancel by system cron job for expired orders
#         SYSTEM = 'ST', _('System')

#     cancel_by = models.CharField(
#         _("cancel by"), max_length=10, choices=Executor.choices, default=Executor.SYSTEM)
#     reason = models.CharField(_("cancel reason"), max_length=250, default='')


#     order = models.OneToOneField(Order, verbose_name=_(
#         "order"), on_delete=models.CASCADE, related_name='cancle_record')


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
    user = models.ForeignKey(User, verbose_name=_(
        "user"), on_delete=models.SET_NULL, null=True, related_name='reviews')

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'review for {self.order_product.product} by {self.order_product.order.user}'
