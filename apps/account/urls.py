from django.urls import path
from .views import (LoginView, LogoutView, RegisterView, ActivateView, PasswordResetView,
                    AccountCenterView, OrderListView, OrderDetailView,
                    AddressView, WishlistView)

app_name = 'account'
urlpatterns = [
    path('', AccountCenterView.as_view(), name='center'),
    path('order/', OrderListView.as_view(), name='order-list'),
    path('order/<slug:number>/', OrderDetailView.as_view(), name='order-detail'),
    path('address/', AddressView.as_view(), name='address'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('register/', RegisterView.as_view(), name='register'),
    path('passwordreset/', PasswordResetView.as_view(), name='password-reset'),
    path('activate/<str:token>/', ActivateView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
