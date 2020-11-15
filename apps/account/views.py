from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.generic import View, CreateView
from django.urls import reverse_lazy, reverse

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from .forms import RegisterForm
from .models import User, Address
from .tasks import send_activation_email

# Create your views here.


class AccountCenterView(LoginRequiredMixin, View):
    template_name = 'account.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        address = Address.objects.get_default_address(user)
        context = {
            'address': address
        }
        return render(request, self.template_name)


class LoginView(SuccessMessageMixin, View):

    template_name = 'login.html'
    success_url = reverse_lazy('shop:index')

    def get(self, request, *args, **kwargs):
        print('cookies', request.COOKIES)
        if 'email' in request.COOKIES:
            email = request.COOKIES.get('email')
            remember = 'checked'
        else:
            email = ''
            remember = ''
        return render(request, 'login.html', {'email': email, 'remember': remember})

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(email=email, password=password)

        if not user:
            messages.error(request, 'Invalid credentials')
            return redirect(reverse('account:login'))

        if not user.is_active:
            messages.error(request, 'Account is not activated')
            return redirect(reverse('account:login'))

        login(request, user)
        remember = request.POST.get('remember')
        next_url = request.GET.get('next', self.success_url)
        response = redirect(next_url)

        if remember == 'on':
            response.set_cookie('email', email, max_age=7*24*3600)
        else:
            response.delete_cookie('email')

        messages.success(request, f'{user.username}, welcome back')
        return response


class LogoutView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            messages.error(request, 'You are not login')
            return redirect(reverse('shop:index'))
        logout(request)
        messages.info(request, 'You have logged out')
        return redirect(reverse('shop:index'))


class RegisterView(SuccessMessageMixin, CreateView):
    form_class = RegisterForm
    template_name = 'register.html'
    success_url = reverse_lazy('shop:index')
    success_message = 'Your account has been created! Check your email for activation.'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = User.objects.create_user(username, email, password)

        serializer = Serializer(settings.SECRET_KEY, 3600*24)
        info = {'activate_user': user.id}
        token = serializer.dumps(info)  # bytes
        token = token.decode()

        send_activation_email.delay(email, username, token)
        messages.success(
            self.request, f'{self.success_message}')

        return HttpResponseRedirect(self.success_url)


class ActivateView(View):
    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600*24)

        try:
            param = serializer.loads(token)
            user_id = param['activate_user']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            messages.success(request, 'Your account has been activated!')
            return redirect(reverse('account:login'))

        except SignatureExpired:
            messages.error(
                request, 'Token expired, please register again!')
            # TODO: set cron job to close account after activation expired
            return redirect(reverse('shop:index'))
