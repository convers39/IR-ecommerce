from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.http import response
from django.shortcuts import render, redirect
from django.views.generic import View, CreateView
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from .forms import RegisterForm, UserLogInForm
from .models import User
from .tasks import send_activation_email

# Create your views here.


class LoginView(SuccessMessageMixin, View):

    form_class = UserLogInForm
    template_name = 'login.html'
    success_message = 'Welcome back!'
    success_url = reverse_lazy('shop:index')

    def get(self, request, *args, **kwargs):
        print(request.COOKIES)
        if 'email' in request.COOKIES:
            email = request.COOKIES.get('email')
            remember = 'checked'
        else:
            email = ''
            remember = ''
        return render(request, 'login.html', {'email': email, 'remember': remember})

    def post(self, request, *args, **kwargs):
        print(request.POST)
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(email=email, password=password)

        if user:
            if user.is_active:
                login(request, user)
                remember = request.POST.get('remember')

                next_url = request.GET.get('next', reverse('shop:index'))
                response = redirect(next_url)

                if remember:
                    response.set_cookie('email', email, max_age=7*24*3600)
                else:
                    response.delete_cookie('email')
                messages.info(request, f'{user.username}, welcome back')
                return response

            else:
                messages.error(request, 'Account is not activated')
                return redirect(reverse('account:login'))
        else:
            messages.error(request, 'Invalid credentials')
            return redirect(reverse('account:login'))


class LogoutView(View):

    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out')
        return redirect(reverse('shop:index'))


class RegisterView(SuccessMessageMixin, CreateView):
    form_class = RegisterForm
    template_name = 'register.html'
    success_url = reverse_lazy('shop:index')
    success_message = 'Your account has been created! Check your email box for activation.'

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
        messages.info(
            self.request, f'{self.success_message}')

        return HttpResponseRedirect(self.success_url)


class ActivateView(View):
    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            user_id = info['activate_user']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            messages.info(request, 'Your account has been activated!')
            return redirect(reverse('account:login'))
        except SignatureExpired:
            messages.error(
                request, 'Token expired, please register again!')
            return redirect(reverse('shop:index'))
