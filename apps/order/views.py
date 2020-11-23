from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin

from shop.models import ProductSKU

# Create your views here.


class OrderConfirmView(View):
    pass
