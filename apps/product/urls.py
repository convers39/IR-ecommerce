from django.urls import path
from .views import ProductListView

app_name = 'product'

urlpatterns = [
    path('list/', ProductListView.as_view(),name='product-list' )
]
