from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import json

from .forms import UserInfoForm
from .models import Address


class AddressManagementMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET':
            return super().dispatch(request, *args, **kwargs)

        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid data'})

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


class AccountInfoCheckMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):

        if request.method == 'POST':
            try:
                data = json.loads(request.body.decode())
            except:
                return JsonResponse({'res': '0', 'errmsg': 'Invalid data'})

            form_fields = set(UserInfoForm().fields.keys())
            data_set = set(key for key in data.keys() if data[key].strip())
            if not form_fields.issubset(data_set):
                return JsonResponse({'res': '0', 'errmsg': 'Incomplete data'})

        return super().dispatch(request, *args, **kwargs)
