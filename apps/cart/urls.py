from django.urls import path
from .views import (CartInfoView, CartAddView,
                    CartUpdateView, CartDeleteView)

app_name = 'cart'
urlpatterns = [
    path('', CartInfoView.as_view(), name='info'),
    path('add/', CartAddView.as_view(), name='add'),
    path('update/', CartUpdateView.as_view(), name='update'),
    path('delete/', CartDeleteView.as_view(), name='delete'),
]
