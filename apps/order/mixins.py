from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

import json

from account.forms import GuestAddressForm
from account.models import Address, User
from shop.models import ProductSKU
from cart.cart import get_user_id, is_first_time_guest, cal_cart_count, get_cart_all_in_order
from .models import Order, OrderProduct


class OrderProcessCheckMixin:
    # TODO: validate guest form data
    def get_post_data(self):
        return json.loads(self.request.body.decode())

    def get_user_and_address(self):
        data = self.get_post_data()
        if self.request.user.is_authenticated:
            addr_id = data.get('addr_id')
            address = Address.objects.get(id=addr_id)
            user = User.objects.get(id=self.request.user.id)
        else:
            user_id = get_user_id(self.request)
            password = User.objects.make_random_password()
            user = User.objects.create(
                username=f'guest_{user_id}',
                email=data['email'],
                password=password
            )
            recipient = data['first_name'] + ' ' + data['last_name']
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

        return user, address

    def dispatch(self, request, *args, **kwargs):
        try:
            data = json.loads(self.request.body.decode())
        except:
            return JsonResponse({'res': 0, 'errmsg': 'Invalid data'})

        payment_method = data.get('payment_method')
        if payment_method not in ['card', 'alipay']:
            return JsonResponse({'res': 0, 'errmsg': 'Invalid payment method'})

        user_id = get_user_id(self.request)
        if is_first_time_guest(request) or cal_cart_count(user_id) == 0:
            return JsonResponse({'res': 0, 'errmsg': 'Cart is empty'})

        sku_list, count_list, ordering = get_cart_all_in_order(user_id)
        qs = ProductSKU.objects.filter(id__in=sku_list).order_by(ordering)
        if len(sku_list) > qs.count():
            # in case before user checkout, item deleted from db,
            # refresh the page will filter out non-existent item
            messages.warning(self.request, 'Item does not exist')
            return redirect(reverse('cart:checkout'))

        for sku, count in zip(qs, count_list):
            if sku.stock < count:
                messages.warning(self.request, f'Item {sku.name} understocked')
                return redirect(reverse('cart:checkout'))

        try:
            User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'res': 0, 'errmsg': 'User does not exist'})

        if self.request.user.is_authenticated:
            addr_id = data.get('addr_id')
            try:
                Address.objects.get(id=addr_id)
            except Address.DoesNotExist:
                messages.error(self.request, 'Address does not exist')
                return JsonResponse({'res': 0, 'errmsg': 'Address does not exist'})
        else:
            # if is guest, check address form data integrity
            form_fields = set(GuestAddressForm().fields.keys())
            data_set = set(key for key in data.keys() if data[key].strip())
            if not form_fields.issubset(data_set):
                return JsonResponse({'res': 0, 'errmsg': 'Address data is incomplete'})

        return super().dispatch(request, *args, **kwargs)


class OrderManagementMixin(LoginRequiredMixin):
    """
    NOTE: if a request comes from a guest, must recheck email and order number
    email and order are sent from frontend, retrieved from url queryparams in order search page,
    which means the guest must search the order first to get the valid url with params
    """

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

        if not request.user.is_authenticated:
            try:
                email = data['email']
                number = data['order_number']
            except KeyError:
                return JsonResponse({'res': '0', 'errmsg': 'Invalid request'})

            user = User.objects.filter(
                Q(email__endswith=email), email=email).first()
            if not user:
                return JsonResponse({'res': '0', 'errmsg': 'Invalid request'})

            try:
                order = Order.objects.get(number=number)
            except Order.DoesNotExist:
                return JsonResponse({'res': '0', 'errmsg': 'Invalid request'})

            if order.user != user:
                return JsonResponse({'res': '0', 'errmsg': 'Invalid request'})

        return super().dispatch(request, *args, **kwargs)


class OrderReviewDataMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})

        op_id = data.get('op_id')
        star = data.get('star')
        comment = data.get('comment')

        if not all([op_id, star, comment]):
            return JsonResponse({'res': '0', 'errmsg': 'Incompleted Data'})

        if len(comment) < 10:
            return JsonResponse({'res': '0', 'errmsg': 'Comment cannot be less than 10 characters'})

        try:
            order_product = OrderProduct.objects.get(id=op_id)
        except OrderProduct.DoesNotExist:
            return JsonResponse({'res': '0', 'errmsg': 'Item does not exist'})

        if order_product.is_reviewed:
            return JsonResponse({'res': '0', 'errmsg': 'You have already reviewed this item'})

        return super().dispatch(request, *args, **kwargs)
