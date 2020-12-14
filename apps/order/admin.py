from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.shortcuts import render
from django.utils.translation import ngettext
from django.http import HttpResponseRedirect


import stripe

from account.tasks import async_send_email
from .models import OrderProduct, Order, Payment, Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    model = Review


class OrderInline(admin.TabularInline):
    model = Order
    exclude = ('is_deleted',)
    max_num = 2
    readonly_fields = ('number', 'status', 'subtotal',
                       'shipping_fee', 'user', 'address',)


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    exclude = ('is_deleted',)
    readonly_fields = ('unit_price', 'count', 'product')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'status',
                    'user', 'payment', 'created_at', 'updated_at',)
    search_fields = ('status', 'user', 'number')
    list_filter = ('status', 'user',)
    readonly_fields = ('is_deleted', 'number', 'status',
                       'subtotal', 'payment', 'user',)
    fieldsets = (
        (None, {
            "fields": (
                'number', 'slug', 'status', 'subtotal', 'shipping_fee'
            ),
        }),
        ('Payment', {
            'fields': (
                'payment', 'user', 'address'
            )
        })
    )
    inlines = [OrderProductInline]
    actions = ['ship_order', 'cancel_order', ]

    def ship_order(self, request, queryset):
        qs = queryset.filter(status="CF").all()
        updated = qs.update(status='SP')
        self.message_user(request, ngettext(
            '%d order was successfully marked as shipped.',
            '%d orders were successfully marked as shipped.',
            updated,
        ) % updated, messages.SUCCESS)
    ship_order.short_description = 'Make selected orders as shipped'
    # add permission for shipping

    def cancel_order(self, request, queryset):
        # only apply to orders requested by guests
        qs = queryset.filter(status='CL').all()
        updated = qs.update(status='CX')
        for order_product in queryset.order_products.all():
            order_product.product.sales -= 1
            order_product.product.stock += 1

        self.message_user(request, ngettext(
            '%d order was successfully marked as cancelled.',
            '%d orders were successfully marked as cancelled.',
            updated,
        ) % updated, messages.SUCCESS)
    cancel_order.short_description = 'Make selected orders as canceled'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'status', 'created_at', 'updated_at',)
    search_fields = ('status', 'number',)
    list_filter = ('status', 'user')
    readonly_fields = ('is_deleted', 'number', 'status',
                       'amount', 'method', 'session_id',)

    fieldsets = (
        (None, {
            "fields": (
                'number', 'status', 'amount', 'method', 'session_id', 'user'
            ),
        }),
    )
    inlines = [OrderInline]
    actions = ['create_refund']

    def create_refund(self, request, queryset):
        return render(request, 'admin/create-refund.html', context={})
        # return HttpResponseRedirect()
        qs = queryset.filter(status="SC").all()
        # check refund amount
        if not amount:
            amount = self.amount
        stripe.api_key = settings.STRIPE_SECRET_KEY
        refund = stripe.Refund.create(
            amount=amount, payment_intent=self.number)
        # send email to costumer
        if refund.status == 'succeeded':
            subject = f'Payment {self.number} Refunded'
            message = f'Payment has been refunded, this will take few days to refund to your account or card.'
            from_email = settings.EMAIL_FROM
            recipient_list = [self.user.email, ]
            async_send_email.delay(
                subject, message, from_email, recipient_list)
        # listen to failed event in webhook
        # create a cancellation record
        updated = qs.update(status='RF')
        self.message_user(request, ngettext(
            '%d order was successfully marked as cancelled.',
            '%d orders were successfully marked as cancelled.',
            updated,
        ) % updated, messages.SUCCESS)
    create_refund.short_description = 'Make refund for payment'
