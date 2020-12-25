from django.http import JsonResponse
from shop.models import ProductSKU
import json


class DataIntegrityCheckMixin:
    def dispatch(self, request, *args, **kwargs):
        # validate data
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': 0, 'errmsg': 'Invalid data'})

        # print(request.data)
        sku_id = data.get('sku_id')
        count = data.get('count')

        if not all([sku_id, count]):
            return JsonResponse({'res': 0, 'errmsg': 'Lack of data'})
        try:
            count = int(count)
        except ValueError:
            return JsonResponse({'res': 0, 'errmsg': 'Invalid item count'})

        try:
            product = ProductSKU.objects.get(id=sku_id)
        except ProductSKU.DoesNotExist:
            return JsonResponse({'res': 0, 'errmsg': 'Item does not exist'})

        if count > product.stock:
            return JsonResponse({'res': 0, 'errmsg': 'Understocked'})

        if count <= 0:
            return JsonResponse({'res': 0, 'errmsg': 'At least 1 item required'})

        return super().dispatch(request, *args, **kwargs)
