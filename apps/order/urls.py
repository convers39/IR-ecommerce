from django.urls import path
from .views import (OrderProcessView, PaymentSuccessView, PaymentRenewView,
                    checkout_webhook, OrderCancelView, OrderSearchView)

app_name = 'order'
urlpatterns = [
    path('process/', OrderProcessView.as_view(), name='process'),
    path('success/', PaymentSuccessView.as_view(), name='success'),
    path('cancel/', OrderCancelView.as_view(), name='cancel'),
    path('search/', OrderSearchView.as_view(), name='search'),
    # path('delete/', OrderDeleteView.as_view(), name='delete'),
    path('paymentrenew/', PaymentRenewView.as_view(), name='payment-renew'),
    path('webhook/', checkout_webhook, name='webhook'),
]
