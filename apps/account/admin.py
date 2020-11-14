from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Address


class AddressInline(admin.StackedInline):
    model = Address
    exclude = ('is_deleted',)
    classes = 'collapse'
    max_num = 3


@admin.register(User)
class UserAdmin(UserAdmin):
    ordering = ('-date_joined', '-last_login')
    list_display = ('username', 'email', 'is_active',
                    'is_staff', 'date_joined', 'last_login')
    search_fields = ('username', 'phone_no', 'email')
    list_filter = ('date_joined', 'username',
                   'is_active', 'is_staff', 'is_superuser')

    fieldsets = (
        ('Information', {
            "fields": (
                'username',
                'first_name',
                'last_name',
                'email',
                'phone_no'
            ),
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
            )
        })
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'first_name',
                'last_name',
                'email',
                'phone_no',
                'password1',
                'password2',
                'is_active',
                'is_staff')}
         ),
    )
    inlines = [AddressInline]
    readonly_fields = ('is_superuser',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipient', 'city',
                    'country', 'zip_code', 'is_default',)
    readonly_fields = ('is_deleted',)


# admin.site.register(User, UserAdmin)
# admin.site.register(Address, AddressAdmin)

# Register your models here.
