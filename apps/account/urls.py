from django.urls import path
from .views import (LoginView, LogoutView, RegisterView, ActivateView,
                    AccountCenterView, AccountOrderListView, AccountOrderDetailView, AccountAddressView)

app_name = 'account'
urlpatterns = [
    path('', AccountCenterView.as_view(), name='center'),
    path('order/', AccountOrderListView.as_view(), name='order-list'),
    # path('order/<int:number>/', AccountOrderDetailView.as_view(), name='order-detail'),
    path('address/', AccountAddressView.as_view(), name='address'),
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<str:token>/', ActivateView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
