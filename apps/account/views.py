from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import query
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import View, CreateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django.views.generic.list import ListView

import json
from django_redis import get_redis_connection

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadData
import stripe

from order.models import Order, OrderProduct, Review
from shop.models import ProductSKU
from order.views import create_checkout_session

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
        # get recent watch history
        conn = get_redis_connection('cart')
        sku_ids = conn.lrange(f'history_{user.id}', 0, 7)

        # NOTE: use filter will break the order of recent products
        # recent_products = ProductSKU.objects.filter(id__in=sku_ids)
        recent_products = []
        for sku_id in sku_ids:
            sku = ProductSKU.objects.get(id=sku_id)
            recent_products.append(sku)

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

        form = UserInfoForm(data, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'res': '1', 'msg': 'Data updated'})

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
    template_name = 'account/order-list.html'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset().select_related('payment')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["count"] = Order.objects.filter(user=self.request.user).count()
        context['stripe_key'] = settings.STRIPE_PUBLIC_KEY
        return context

    def get_queryset(self):
        return super().get_queryset()


class PaymentRenewView(View):
    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})
        print(data)

        order_id = data.get('order_id')
        order = Order.objects.select_related('payment').get(id=order_id)
        payment = order.payment
        method = payment.method
        name = f'Retry payment for order# {order.number}'
        amount = payment.amount
        try:
            session = create_checkout_session(
                user, method, name, amount)
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Failed to renew payment session'})

        payment.renew_payment(session)
        return JsonResponse({
            'res': 1,
            'session': session,
            'msg': 'Payment session renewed'
        })


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    context_object_name = 'order'
    template_name = 'account/order-detail.html'
    slug_url_kwarg = 'number'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order_products"] = self.object.order_products.all(
        ).select_related('product')
        payment = self.object.payment
        payment_intent = stripe.PaymentIntent.retrieve(
            payment.number)
        context['stripe_key'] = settings.STRIPE_PUBLIC_KEY
        if payment.status != 'SC':
            context['payment_detail'] = None
        else:
            context['payment_detail'] = payment_intent.charges.data[0].payment_method_details
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            data = json.loads(request.body.decode())
        except:
            return JsonResponse({'res': '0', 'errmsg': 'Invalid Data'})
        print(data)

        order_product_id = data.get('order_product_id')
        star = data.get('star')
        comment = data.get('comment')

        try:
            order_product = OrderProduct.objects.get(id=order_product_id)
        except OrderProduct.DoesNotExist:
            return JsonResponse({'res': '0', 'errmsg': 'Item does not exist'})

        Review.objects.create(
            order_product=order_product,
            star=star,
            comment=comment
        )
        return JsonResponse({'res': '1', 'msg': 'Comment submitted'})


class OrderCancelView(View):
    def post(self, request, *args, **kwargs):
        return JsonResponse()


class AddressView(LoginRequiredMixin, FormMixin, View):
    model = Address
    form_class = AddressForm
    template_name = 'account/address.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        addresses = user.addresses.all()
        context = {
            'user': user,
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

        # delete existed address
        if data.get('operation') == 'delete':
            try:
                Address.objects.filter(id=data['addr_id']).delete()
                return JsonResponse({'res': '1', 'msg': 'Address deleted'})
            except Address.DoesNotExist:
                return JsonResponse({'res': '0', 'errmsg': 'Address does not exist'})

        # save new address
        form = AddressForm(data)
        if form.is_valid():
            new_addr = form.save(commit=False)
            new_addr.user = user
            new_addr.save()
            new_id = new_addr.id
            return JsonResponse({'res': '1', 'msg': 'New address added', 'new_id': new_id})

        return JsonResponse({'res': '0', 'errmsg': 'Error!'})

        # TODO: update existed address
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


class WishlistView(LoginRequiredMixin, ListView):
    model = ProductSKU
    context_object_name = 'products'
    paginate_by = 10  # TODO: solve pagination issue when delete item from frontend
    template_name = 'account/wishlist.html'

    def get_queryset(self):
        user = self.request.user
        conn = get_redis_connection('cart')
        wishlisted = conn.smembers(f'wish_{user.id}')
        queryset = ProductSKU.objects.filter(id__in=wishlisted)
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
