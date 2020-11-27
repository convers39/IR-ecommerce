from django.urls import path
from .views import LoginView, LogoutView, RegisterView, ActivateView, AccountCenterView

app_name = 'account'
urlpatterns = [
    path('', AccountCenterView.as_view(), name='center'),
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<str:token>', ActivateView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
