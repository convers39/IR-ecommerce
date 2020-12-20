from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, response
from django.contrib import messages

import json

from account.models import Address, User
from cart.cart import get_user_id, is_first_time_guest
from .models import Order


class OrderDataCheckMixin:
    # TODO: validate guest form data
    def get_post_data(self):
        try:
            data = json.loads(self.request.body.decode())
        except:
            return JsonResponse({'res': 0, 'errmsg': 'Invalid data'})
        return data

    def get_user_and_address(self):
        data = self.get_post_data()
        if self.request.user.is_authenticated:
            addr_id = data.get('addr_id')
            try:
                address = Address.objects.get(id=addr_id)
            except Address.DoesNotExist:
                return JsonResponse({'res': 0, 'errmsg': 'Address does not exist'})
            try:
                user = User.objects.get(id=self.request.user.id)
            except User.DoesNotExist:
                return JsonResponse({'res': 0, 'errmsg': 'User does not exist'})
        else:
            user_id = get_user_id(self.request)
            password = User.objects.make_random_password()
            user = User.objects.create(
                username=f'guest_{user_id}',
                email=data['email'],
                password=password
            )
            recipient = data['first_name'] + ' ' + data['last_name']
            try:
                address = Address.objects.create(
                    recipient=recipient,
                    phone_no=data['phone_no'],
                    addr=data['addr'],
                    city=data['city'],
                    province=data['province'],
                    country=data['country'],
                    zip_code=data['zip_code'],
                    user=user
                )
            except KeyError:
                return JsonResponse({'res': 0, 'errmsg': 'Address data is incomplete'})

        return user, address

    def dispatch(self, request, *args, **kwargs):
        # validate data
        data = self.get_post_data()
        if is_first_time_guest(request):
            return JsonResponse({'res': 0, 'errmsg': 'Cart is empty'})

        payment_method = data.get('payment_method')
        if payment_method not in ['card', 'alipay']:
            return JsonResponse({'res': 0, 'errmsg': 'Invalid payment method'})

        return super().dispatch(request, *args, **kwargs)


class OrderManagementMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})

        order_id = data.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({'res': '0', 'errmsg': 'Order does not exist'})

        return super().dispatch(request, *args, **kwargs)
