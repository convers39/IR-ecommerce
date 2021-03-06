from django.urls import path
from .views import IndexView, ProductListView, ProductDetailView


app_name = 'shop'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('shop/', ProductListView.as_view(), name='product-list'),
    path('shop/<slug:category_slug>/',
         ProductListView.as_view(), name='category-list'),
    path('shop/<int:pk>/<slug:slug>/',
         ProductDetailView.as_view(), name='product-detail'),
]
