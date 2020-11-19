from django.urls import path
from .views import IndexView,  ProductListView, ProductDetailView, CategoryListView, ProductSearchView

app_name = 'shop'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('shop/', ProductListView.as_view(), name='product-list'),
    path('shop/search/', ProductSearchView.as_view(), name='product-search'),
    path('shop/<slug:category_slug>/',
         CategoryListView.as_view(), name='category-list'),
    path('shop/<int:pk>/<slug:slug>/',
         ProductDetailView.as_view(), name='product-detail'),
]
