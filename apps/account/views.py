from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import View, CreateView
from django.views.generic.edit import FormMixin
from django.views.generic.list import ListView

import json

from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadData

from cart.cart import get_watch_history_products
from order.models import Order
from shop.models import ProductSKU

from .forms import RegisterForm, UserInfoForm, AddressForm, create_address_formset
from .models import User, Address
from .mixins import AddressManagementMixin
from .tasks import send_activation_email


class AccountCenterView(LoginRequiredMixin, FormMixin, View):
    model = User
    form_class = UserInfoForm
    template_name = 'account/account.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        form = UserInfoForm(instance=user)
        # get recent watch history
        recent_products = get_watch_history_products(user.id)

        context = {
            'user': user,
            'form': form,
            'recent_products': recent_products
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})
        print(data)

        msg = 'Data updated'
        if data['email'] != user.email:
            # send activate email
            new_email = data['email']
            send_activation_email.delay(new_email, user.username, user.id)
            data['email'] = user.email
            msg = 'Email address will be updated after your verification'
        form = UserInfoForm(data, instance=user)

        if form.is_valid():
            form.save()
            return JsonResponse({'res': '1', 'msg': msg})

        return JsonResponse({'res': '0', 'errmsg': 'Invalid form data'})


class PasswordResetView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})
        print(data)

        current = data.get('currentPassword')
        new = data.get('newPassword')
        confirm = data.get('confirmNewPassword')

        if new != confirm:
            return JsonResponse({'res': '0', 'errmsg': 'Passwords does not match'})

        if not user.check_password(current):
            return JsonResponse({'res': '0', 'errmsg': 'Current password invalid'})

        if new == current:
            return JsonResponse({'res': '0', 'errmsg': 'Same as current password'})

        user.set_password(new)
        user.save()
        # TODO: send email to customer
        return JsonResponse({'res': '1', 'msg': 'Password changed'})


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    context_object_name = 'orders'
    template_name = 'account/order.html'
    paginate_by = 4

    def get_queryset(self):
        queryset = super().get_queryset().filter(Q(user=self.request.user), is_deleted=False)\
            .select_related(*['address', 'payment'])\
            .prefetch_related(*['order_products__product', 'order_products__review'])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_key'] = settings.STRIPE_PUBLIC_KEY
        return context


class AddressView(AddressManagementMixin, FormMixin, View):
    model = Address
    form_class = AddressForm
    template_name = 'account/address.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        addresses = user.addresses.all()
        # formset = create_address_formset(user)
        context = {
            'user': user,
            'addresses': addresses,
            'form': self.form_class,
            # 'formset': formset
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        data = json.loads(request.body.decode())

        form = AddressForm(data)
        if form.is_valid():
            new_addr = form.save(commit=False)
            new_addr.user = user
            new_addr.save()
            if data.get('setDefault') == 'on':
                new_addr.set_default_address(request.user)
            new_id = new_addr.id
            return JsonResponse({'res': '1', 'msg': 'New address added', 'new_id': new_id})
        else:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid form data'})

    def put(self, request, *args, **kwargs):
        data = json.loads(request.body.decode())
        address = Address.objects.get(id=data.pop('addr_id'))

        form = AddressForm(instance=address, data=data)
        if form.is_valid():
            updated_addr = form.save()
            updated_id = updated_addr.id
            if data.get('setDefault') == 'on':
                updated_addr.set_default_address(request.user)
            return JsonResponse({'res': '1', 'msg': 'Address updated', 'updated_id': updated_id})
        else:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid form data'})

    def delete(self, request, *args, **kwargs):
        data = json.loads(request.body.decode())

        Address.objects.filter(id=data['addr_id']).delete()
        return JsonResponse({'res': '1', 'msg': 'Address deleted'})


class WishlistView(LoginRequiredMixin, ListView):
    model = ProductSKU
    context_object_name = 'products'
    paginate_by = 10  # TODO: solve pagination issue when delete item from frontend
    template_name = 'account/wishlist.html'

    def get_queryset(self):
        user = self.request.user
        conn = get_redis_connection('cart')
        wishlisted = conn.smembers(f'wish_{user.id}')
        queryset = ProductSKU.objects.prefetch_related(
            'tags').filter(id__in=wishlisted)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context[""] =
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            data = json.loads(request.body.decode())
            sku_id = data['sku_id']
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})
        print(data)

        try:
            ProductSKU.objects.filter(id=sku_id)
        except ProductSKU.DoesNotExist:
            return JsonResponse({'res': '0', 'errmsg': 'Item does not exist'})

        conn = get_redis_connection('cart')
        wish_key = f'wish_{user.id}'
        wish_count = conn.scard(wish_key)
        # check if in wishlist already
        if conn.sismember(wish_key, sku_id):
            conn.srem(wish_key, sku_id)
            return JsonResponse({
                'res': 1,
                'msg': 'Item removed from wishlist',
                'wish_count': int(wish_count) - 1
            })
        # if not add to list
        conn.sadd(wish_key, sku_id)
        return JsonResponse({
            'res': 1,
            'msg': 'Item added to wishlist',
            'wish_count': int(wish_count) + 1
        })


class LoginView(SuccessMessageMixin, View):
    template_name = 'account/login.html'
    success_url = reverse_lazy('shop:index')

    def get(self, request, *args, **kwargs):
        # TODO: check cookie setting logic
        print('login view user', request.user)
        if 'email' in request.COOKIES:
            email = request.COOKIES.get('email')
            remember = 'on'
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

        if remember == 'on':  # either on or none
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
    """
    If new created user has ordered with the same email address as guest,
    transfer guest account data to new created user.
    """
    form_class = RegisterForm
    template_name = 'account/register.html'
    success_url = reverse_lazy('shop:index')
    success_message = 'Your account has been created! Check your email for activation.'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = User.objects.create_user(username, email, password)

        # NOTE: merge guest account
        guest_email = 'guest_'+email
        guest_user = User.objects.filter(email=guest_email).first()
        if guest_user:
            user.payments.set(guest_user.payments.all())
            user.orders.set(guest_user.orders.all())
            user.addresses.set(guest_user.addresses.all())
            guest_user.delete()

        send_activation_email.delay(email, username, user.id)
        messages.success(
            self.request, f'{self.success_message}')

        return HttpResponseRedirect(self.success_url)


class ActivateView(View):
    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600*24)

        try:
            param = serializer.loads(token)
            print(param)
            user_id = param['activate_user']
            email = param['email']
            user = User.objects.get(id=user_id)
            if user.is_active:
                # change email for user
                user.email = email
                user.save()
                logout(request)
                messages.success(
                    request, 'Your email address has been changed!')
            else:
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
