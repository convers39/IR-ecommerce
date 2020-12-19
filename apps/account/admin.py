from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simpleui.admin import AjaxAdmin
from django.http.response import JsonResponse

from .models import User, Address


class AddressInline(admin.StackedInline):
    model = Address
    readonly_fields = ('is_deleted', 'is_default')
    classes = 'collapse'
    max_num = 3


@admin.register(User)
class UserAdmin(UserAdmin):
    ordering = ('-date_joined', '-last_login')
    list_display = ('id', 'username', 'email', 'is_active',
                    'is_staff', 'date_joined', 'last_login')
    search_fields = ('username', 'phone_no', 'email')
    list_filter = ('date_joined', 'username',
                   'is_active', 'is_staff', 'is_superuser')

    fieldsets = (
        ('Information', {
            "fields": (
                'username', 'first_name', 'last_name', 'email', 'phone_no'
            ),
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
            )
        })
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'first_name', 'last_name', 'email',
                'phone_no', 'password1', 'password2',
                'is_active', 'is_staff'
            )}
         ),
    )
    inlines = [AddressInline]
    readonly_fields = ('is_superuser',)


@admin.register(Address)
class AddressAdmin(AjaxAdmin):
    list_display = ('user', 'recipient', 'city',
                    'country', 'zip_code', 'is_default',)
    ordering = ('user',)
    search_fields = ('user',)
    list_select_related = ('user',)
    readonly_fields = ('is_deleted', 'is_default')

    actions = ['set_default', ]

    def set_default(self, request, queryset):

        post = request.POST
        addr_id = post.get('_selected')
        if not addr_id:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'No address selected'
            })

        ids = addr_id.split(',')
        # print('qs', queryset, request.POST)
        if len(ids) > 1:
            return JsonResponse(data={
                'status': 'error',
                'msg': 'You can only set one default address'
            })
        addr = Address.objects.select_related('user').get(id=addr_id)
        user = addr.user
        addr.set_default_address(user)

        return JsonResponse(data={
            'status': 'success',
            'msg': 'Selected address has been set as default'
        })

    set_default.short_description = ' Set Default'
    set_default.type = 'secondary'
    set_default.icon = 'fas fa-shipping-fast'
    set_default.layer = {
        'title': 'Set Address As Default',
        'tips': 'This operation can only be applied to one object.\
            Selected address will be set as the default shipping address.\
            Current default address will be reset.',
        'confirm_button': 'confirm',
        'cancel_button': 'cancel',
        'width': '50%',
        'labelWidth': '50%',
        'params': [{
            'type': 'checkbox',
            'key': 'confirmed',
            'value': [],
            'label': 'Confirm on change?',
            'require':True,
            'options': [{
                'key': '0',
                'label': 'Yes, no problem'
            }]
        }, ]
    }
