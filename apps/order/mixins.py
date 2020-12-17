from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from account.models import Address
from .models import Order
import json


class OrderDataCheckMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        # validate data
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': 0, 'errmsg': 'Invalid data'})

        addr_id = data.get('addr_id')
        payment_method = data.get('payment_method')
        if not all([addr_id, payment_method]):
            return JsonResponse({'res': 0, 'errmsg': 'Lack of data'})

        try:
            Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 0, 'errmsg': 'Address does not exist'})

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
