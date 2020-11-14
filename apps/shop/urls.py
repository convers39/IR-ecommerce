from django.urls import path
from .views import ProductListView, IndexView

app_name = 'shop'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('list/', ProductListView.as_view(), name='product-list')
]
