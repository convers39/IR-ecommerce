from django.contrib import admin


from .models import OrderProduct, Order, Payment, Review


class OrderInline(admin.TabularInline):
    model = Order
    exclude = ('is_deleted',)
    max_num = 2
    readonly_fields = ('number', 'status', 'subtotal',
                       'shipping_fee', 'user', 'address',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'status', 'user', 'payment', 'created_at')
    search_fields = ('status', 'user', 'number')
    list_filter = ('status', 'user',)
    readonly_fields = ('is_deleted', 'number', 'status',
                       'subtotal', 'payment', 'user',)
    fieldsets = (
        (None, {
            "fields": (
                'number', 'status', 'subtotal', 'shipping_fee'
            ),
        }),
        ('Payment', {
            'fields': (
                'payment', 'user', 'address'
            )
        })
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('number', 'status', 'created_at',)
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
