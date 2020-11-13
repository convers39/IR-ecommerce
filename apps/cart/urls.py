from django.urls import path
from .views import CartInfoView

app_name = 'cart'
urlpatterns = [
    path('', CartInfoView.as_view(), name='cart_info'),
]
