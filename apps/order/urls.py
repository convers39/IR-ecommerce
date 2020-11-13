from django.urls import path
from .views import OrderConfirmView

app_name = 'order'
urlpatterns = [
    path('confirm/', OrderConfirmView.as_view(), name='order-confirm'),
]
