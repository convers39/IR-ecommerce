from django.http import JsonResponse
from shop.models import ProductSKU


class DataIntegrityCheckMixin:
    def dispatch(self, request, *args, **kwargs):
        # validate data
        if not request.user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': 'Login required'})

        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        if not all([sku_id, count]):
            return JsonResponse({'res': 0, 'errmsg': 'Invalid data'})
        try:
            count = int(count)
        except ValueError:
            return JsonResponse({'res': 0, 'errmsg': 'Invalid data'})

        try:
            product = ProductSKU.objects.get(id=sku_id)
        except ProductSKU.DoesNotExist:
            return JsonResponse({'res': 0, 'errmsg': 'Item not exist'})

        if count > product.stock:
            return JsonResponse({'res': 0, 'errmsg': 'Understocked'})

        return super().dispatch(request, *args, **kwargs)
