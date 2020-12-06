from django.http import JsonResponse
from shop.models import ProductSKU
from account.models import Address
import json


class OrderDataCheckMixin:
    def dispatch(self, request, *args, **kwargs):
        # validate data
        if not request.user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': 'Please login'})

        try:
            data = json.loads(request.body.decode())
            addr_id = data.get('addr').split('-')[-1]
            payment_method = data.get('payment_method')
        except:
            return JsonResponse({'res': 0, 'errmsg': 'Invalid data'})

        if not all([addr_id, payment_method]):
            return JsonResponse({'res': 0, 'errmsg': 'Lack of data'})

        try:
            Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 0, 'errmsg': 'Address does not exist'})

        return super().dispatch(request, *args, **kwargs)
