import json
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import View, CreateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin, UpdateView
from django.views.generic.list import ListView, MultipleObjectMixin

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadData

from order.models import Order

from .forms import RegisterForm, UserInfoForm, AddressForm
from .models import User, Address
from .tasks import send_activation_email


class AccountCenterView(LoginRequiredMixin, FormMixin, View):
    model = User
    form_class = UserInfoForm
    template_name = 'account/account.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        form = UserInfoForm(instance=user)
        context = {
            'user': user,
            'form': form
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})
        print(data)

        form = UserInfoForm(data, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'res': '1', 'msg': 'Data updated'})

        return JsonResponse({'res': '0', 'errmsg': 'Error!'})


class AccountOrderListView(LoginRequiredMixin, ListView):
    model = Order
    context_object_name = 'orders'
    template_name = 'account/order-list.html'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["count"] = Order.objects.filter(user=self.request.user).count()
        context['stripe_key'] = settings.STRIPE_PUBLIC_KEY
        return context

    def get_queryset(self):
        return super().get_queryset()


class AccountOrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    context_object_name = 'order'
    template_name = 'account/order-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order_products"] = self.object.order_products
        return context


class AccountAddressView(LoginRequiredMixin, FormMixin, View):
    model = Address
    form_class = AddressForm
    template_name = 'account/address.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        addresses = user.addresses.all()
        # forms = [AddressForm(instance=address) for address in all_addresses]
        # default_addr = Address.objects.get_default_address(user)
        context = {
            'user': user,
            # 'default_addr': default_addr,
            'addresses': addresses,
            'form': self.form_class
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})
        print(data)

        if data.get('operation') == 'delete':
            try:
                Address.objects.filter(id=data['addr_id']).delete()
                return JsonResponse({'res': '1', 'msg': 'Address deleted'})
            except Address.DoesNotExist:
                return JsonResponse({'res': '0', 'errmsg': 'Address does not exist'})

        form = AddressForm(data)
        if form.is_valid():
            new_addr = form.save(commit=False)
            new_addr.user = user
            new_addr.save()

            return JsonResponse({'res': '1', 'msg': 'Data updated'})

        return JsonResponse({'res': '0', 'errmsg': 'Error!'})

        # TODO: check if addr already existed or create newone
        # addr_id = data.pop('addr_id')
        # if addr_id:
        #     try:
        #         addr = Address.objects.get(id=addr_id)
        #     except Address.DoesNotExist:
        #         return JsonResponse({'res': '0', 'errmsg': 'Address does not exist'})

        #     if addr.user != user:
        #         return JsonResponse({'res': '0', 'errmsg': 'Unauthorized user'})

        #     form = AddressForm(data, instance=addr)
        # else:


class LoginView(SuccessMessageMixin, View):
    template_name = 'account/login.html'
    success_url = reverse_lazy('shop:index')

    def get(self, request, *args, **kwargs):
        # TODO: check cookie setting logic
        if 'email' in request.COOKIES:
            email = request.COOKIES.get('email')
            remember = 'checked'
        else:
            email = ''
            remember = ''
        return render(request, self.template_name, {'email': email, 'remember': remember})

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(email=email, password=password)

        if not user:
            messages.error(request, 'Invalid credentials.')
            return redirect(reverse('account:login'))

        if not user.is_active:
            messages.error(request, 'Account is not activated.')
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
    template_name = 'account/register.html'
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

        except BadData:
            messages.error(request, 'Invalid request!')
            return redirect(reverse('shop:index'))
