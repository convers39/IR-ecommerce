from django.contrib import admin
from django.db.models import Sum, Q, F, Prefetch
from django.http.response import JsonResponse

from simpleui.admin import AjaxAdmin

from account.tasks import send_order_email, send_refund_email
from .models import OrderProduct, Order, Payment, Review
# from .actions import create_refund


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    model = Review
    list_select_related = ('order_product', 'user',)


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
    list_select_related = ('product', 'order',)


@admin.register(Order)
class OrderAdmin(AjaxAdmin):
    list_display = ('id', 'number', 'status',
                    'user', 'payment', 'created_at', 'updated_at',)
    search_fields = ('status', 'user', 'number')
    list_filter = ('status', 'user', 'created_at')
    list_select_related = ('payment', 'user', 'address',)
    readonly_fields = ('is_deleted', 'number', 'status',
                       'subtotal', 'payment', 'user',)
    fieldsets = (
        ('Order Info', {
            "fields": (
                'number', 'slug', 'status', 'subtotal', 'shipping_fee', 'is_deleted'
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

    def has_ship_order_permission(self, request):
        opts = self.opts
        return request.user.has_perm(f'{opts.app_label}.ship_order')

    def has_cancel_order_permission(self, request):
        opts = self.opts
        return request.user.has_perm(f'{opts.app_label}.cancel_order')

    def ship_order(self, request, queryset):
        post = request.POST
        order_id = post.get('_selected')
        if not order_id:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'No order selected'
            })

        ids = order_id.split(',')
        orders = Order.objects.select_related(
            'user').filter(Q(id__in=ids), status='CF')
        # print('qs', queryset, request.POST)
        if not orders:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'None of selected order can be shipped'
            })

        for order in orders:
            order.ship()
            order.save()
            send_order_email.delay(
                order.user.email, order.user.username, order.number, order.status)

        return JsonResponse(data={
            'status': 'success',
            'msg': 'Selected orders are marked as shipped'
        })

    ship_order.short_description = ' Ship'
    ship_order.allowed_permissions = ('ship_order',)
    ship_order.type = 'secondary'
    ship_order.icon = 'fas fa-shipping-fast'
    ship_order.layer = {
        'title': 'Ship Orders',
        'tips': 'You can ship multiple orders simultaneously, this operation CANNOT be canceled.',
        'confirm_button': 'confirm',
        'cancel_button': 'cancel',
        'width': '50%',
        'labelWidth': '50%',
        'params': [{
            'type': 'checkbox',
            'key': 'confirmed',
            'value': [],
            'label': 'Confirm on shipment?',
            'require':True,
            'options': [{
                'key': '0',
                'label': 'Yes, no problem'
            }]
        }, ]
    }
    # add permission for shipping

    def cancel_order(self, request, queryset):
        """
        Use this action to cancel or refund an order as the first choice.
        Every payment can  berefunded only once.
        As an alternative refund could be operated on Stripe Dashboard.
        In the case of using Stripe Dashboard for refund, add refund events to webhook
        """
        post = request.POST
        order_id = post.get('_selected')
        if not order_id:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'No order selected'
            })

        ids = order_id.split(',')
        refund = post.get('refund')
        amount = post.get('amount')

        if len(ids) > 1 and not amount:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'Cannot apply same refund amount to multiple orders'
            })

        if amount:
            try:
                amount = int(amount)
            except:
                return JsonResponse(data={
                    'status': 'error',
                    'msg': 'Invalid input amount'
                })

        orders = Order.objects.filter(
            Q(id__in=ids), status='CL').select_related('payment')
        # print('qs', queryset, request.POST)
        if not orders:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'None of selected order can be cancelled'
            })

        for order in orders:
            order.confirm_cancel()
            order.save()
            send_order_email.delay(
                order.user.email, order.user.username, order.number, order.status)
            order.restore_product_stock()

            if refund == 'YES':
                payment = order.payment
                refund_amount = order.subtotal if not amount else amount
                payment.refund(refund_amount)
                payment.save()
                # send refund email
                send_refund_email.delay(
                    order.user.email, order.user.username, order.number, refund_amount)

        return JsonResponse(data={
            'status': 'success',
            'msg': 'Selected orders are cancelled'
        })

    cancel_order.short_description = ' Cancel'
    cancel_order.type = 'danger'
    cancel_order.icon = 'fas fa-times'
    cancel_order.layer = {
        'title': 'Cancel Orders',
        'tips': 'You can cancel multiple orders simultaneously. \
            As default the system will use the order subtotal as the refund amount.\
            You cannot make refund to multiple orders with an entered amount,\
            this operation CANNOT be canceled.',
        'confirm_button': 'confirm',
        'cancel_button': 'cancel',
        'width': '50%',
        'labelWidth': '50%',
        'params': [{
            'type': 'radio',
            'key': 'refund',
            'label': 'Create refund?',
            'require': True,
            'options': [{
                'key': '0',
                'label': 'NO'
            }, {
                'key': '1',
                'label': 'YES'
            }]},
            {'type': 'input',
             'key': 'amount',
             'label': 'Refund Amount (JPY)',
             },
            {'type': 'checkbox',
             'key': 'confirmed',
             'value': [],
             'label': 'Confirm to cancel?',
             'require':True,
             'options': [{
                     'key': '0',
                     'label': 'Yes, no problem'
             }]
             }, ]
    }


@ admin.register(Payment)
class PaymentAdmin(AjaxAdmin):
    list_display = ('id', 'number', 'status', 'created_at', 'updated_at',)
    search_fields = ('status', 'number',)
    list_filter = ('status', 'user', 'created_at')
    list_select_related = ('user',)
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
    actions = ['create_refund', ]

    def has_refund_permission(self, request):
        opts = self.opts
        return request.user.has_perm(f'{opts.app_label}.refund')

    def create_refund(self, request, queryset):
        """
        Retrieve payment instances with the sum of related orders subtotal,
        orders must be in the status of cancelling or returning.
        Use this action only when refunding multiple orders in a same Payment instance.
        NOTE: the SUM amount of all related orders will be the total refund amount,
        in some rare cases (e.g. 2 related orders under cancelling, while only 1 is OK to cancel)
        this will lead to trouble on refunding, to make sure cancel only 1 singel order, 
        use cancel action in Order page instead.
        """
        post = request.POST
        amount = post.get('amount')
        payment_id = post.get('_selected')
        ids = payment_id.split(',')
        # print('qs', queryset, request.POST)

        if not payment_id:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'No payment selected'
            })

        if len(ids) > 1 and not amount:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'Cannot refund same amount to multiple payments'
            })

        if amount:
            try:
                amount = int(amount)
            except:
                return JsonResponse(data={
                    'status': 'error',
                    'msg': 'Invalid amount'
                })

        payments = Payment.objects.filter(Q(id__in=ids), status='SC').prefetch_related(
            Prefetch('orders', queryset=Order.objects.filter(status__in=['CL', 'RT'])))\
            .annotate(refund_amount=Sum('orders__subtotal'))

        if not payments:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'No refundable payment'
            })

        for payment in payments:
            amount = payment.refund_amount
            payment.refund(amount)
            payment.save()
            # send refund email
            for order in payment.orders.select_related('user').filter(status__in=['CL', 'RT']):
                order.confirm_cancel()
                order.save()
                send_order_email.delay(
                    order.user.email, order.user.username, order.number, order.status)
                order.restore_product_stock()
            number = payment.orders.first().number  # pick one order number
            send_refund_email(
                payment.user.email, payment.user.username, number, amount)
            # listen to failed event in webhook
            # create a cancellation record
        return JsonResponse(data={
            'status': 'success',
            'msg': 'Refund created'
        })

    # config for create refund modal window
    create_refund.short_description = ' Refund'
    create_refund.type = 'danger'
    create_refund.icon = 'fas fa-hand-holding-usd'
    create_refund.layer = {
        'title': 'Make a refund',
        'tips': 'If no amount is entered, as default system will refund the subtotal except shipping fee,\
            this can be applied to multiple instances.\
            You cannot make refund to multiple payments with an entered amount.',
        'confirm_button': 'confirm',
        'cancel_button': 'cancel',
        'width': '50%',
        'labelWidth': '50%',
        'params': [{
            'type': 'input',
            'key': 'amount',
            'label': 'Refund Amount (JPY)',
        }, {
            'type': 'checkbox',
            'key': 'confirmed',
            'value': [],
            'label': 'CANNOT BE CANCELED!',
            'require':True,
            'options': [{
                'key': '0',
                'label': 'Yes, no problem'
            }]
        }, ]
    }
