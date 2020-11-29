from django.urls import path
from .views import CheckoutView, OrderProcessView, PaymentSuccessView, checkout_webhook

app_name = 'order'
urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('process/', OrderProcessView.as_view(), name='process'),
    path('success/', PaymentSuccessView.as_view(), name='success'),
    path('webhook/', checkout_webhook, name='webhook'),
]
