from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView

import logging

from django_redis import get_redis_connection

from .models import ProductSKU, Category, HomeBanner

logger = logging.getLogger(__name__)


class IndexView(ListView):
    template_name = 'index.html'
    context_object_name = 'products'

    def get_queryset(self):
        try:
            queryset = ProductSKU.objects.get_trending_products().\
<<<<<<< HEAD
                order_by('?')[:8]
=======
                order_by('?')[:7]
            # logger.info('fetch database for index page')
>>>>>>> guestcheckout
        except ValueError:
            queryset = []
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: implement slide for banners
        context["banners"] = HomeBanner.objects.all()
        return context


class ProductListView(ListView):
    model = ProductSKU
    context_object_name = 'products'
    template_name = 'shop/product-list.html'
    paginate_by = 3
    paginate_orphans = 1

    def get_ordering(self):
        ordering = self.request.GET.get('sorting', '-created_at')
        # validate ordering
        if ordering not in ['-created_at', 'sales', 'price', '-price']:
            messages.info(self.request, 'Sorted by default (latest).')
            ordering = '-created_at'
        return ordering

    def get_queryset(self):
        queryset = super().get_queryset()

        # check if user input a search text, consider to asign seperate route for search
        search_term = self.request.GET.get('search')
        if search_term:
            queryset = ProductSKU.objects.search(search_term)

        # check if search by category
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = ProductSKU.objects.filter_category_products(
                category, queryset)

        # check if search by tag
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__name__in=[tag])
        if queryset.count() == 0:
            messages.error(self.request, 'No results found!')
        queryset = queryset.order_by(self.get_ordering())

        # check if item is wishlisted
        user = self.request.user
        if user.is_authenticated:
            queryset = ProductSKU.objects.filter_wishlisted_products(
                user.id, queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = category_slug.replace('-', ' ')
            if 'and' in category:
                category = category.replace('and', '&')
            context['category'] = category

        return context


class ProductDetailView(DetailView):
    model = ProductSKU
    context_object_name = 'product'
    template_name = 'shop/product-detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        # add view history, share same redis server with cart, saved as list
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection('cart')
            history_key = f'history_{user.id}'
            product_id = self.object.id
            # remove product if already existed in history
            conn.lrem(history_key, 0, product_id)
            # push current product to the beginning of list
            conn.lpush(history_key, product_id)
            # only save 8 historical products
            conn.ltrim(history_key, 0, 7)

            wishlisted = conn.sismember(f'wish_{user.id}', product_id)
            if wishlisted:
                self.object.wishlist = True

        return self.render_to_response(context)

    def get_queryset(self):
        return super().get_queryset().select_related('category')\
            .prefetch_related('order_products__review')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context['images'] = product.images.all()
        context['related_products'] = ProductSKU.objects.get_related_products(
            product)[:4]

<<<<<<< HEAD
        context['reviews'] = [order_product.review for order_product in product.order_products.all(
        ) if order_product.is_reviewed]
=======
        context['reviews'] = [
            op.review for op in product.order_products.all() if op.is_reviewed]
>>>>>>> guestcheckout
        return context
