from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json

from account.models import Address


class AddressManagementMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET':
            return super().dispatch(request, *args, **kwargs)

        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})

        if request.method in ['DELETE', 'PUT']:
            try:
                addr_id = data.pop('addr_id')
            except KeyError:
                return JsonResponse({'res': '0', 'errmsg': 'Address id is missing'})
            try:
                address = Address.objects.get(id=addr_id)
            except Address.DoesNotExist:
                return JsonResponse({'res': '0', 'errmsg': 'Address does not exist'})

        return super().dispatch(request, *args, **kwargs)
