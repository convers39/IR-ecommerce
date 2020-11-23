from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin


from django_redis import get_redis_connection

from shop.models import ProductSKU, Category

# Create your views here.


class CartAddView(View):
    def post(self, request):
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')


class CartInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        conn = get_redis_connection('cart')
        cart_key = f'cart_{user.id}'
        cart_dict = conn.hgetall(cart_key)

        products = []
        total_count = 0
        total_price = 0
        for product_id, count in cart_dict.items():
            product = ProductSKU.objects.get(id=product_id)
            amount = product.price * int(count)
            product.amount = amount
            product.count = count
            products.append(product)

            total_count += int(count)
            total_price += amount
        categories = Category.objects.all()
        context = {
            'total_count': total_count,
            'total_price': total_price,
            'products': products,
            'categories': categories,
        }

        return render(request, 'cart/cart.html', context)


class CartUpdateView(View):

    pass


class CartDeleteView(View):
    pass
