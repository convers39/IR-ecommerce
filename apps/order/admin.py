from django.contrib import admin
from django.contrib.admin.decorators import register


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
                    'user', 'payment', 'created_at')
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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'status', 'created_at',)
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
