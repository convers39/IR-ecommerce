from django.shortcuts import render
from django.views.generic import ListView, View

# Create your views here.


class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')


class ProductListView(ListView):
    pass
