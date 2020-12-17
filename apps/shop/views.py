from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView

from django_redis import get_redis_connection

from .models import ProductSKU, Category, HomeBanner


class IndexView(ListView):
    template_name = 'index.html'
    context_object_name = 'products'
    # NOTE: By only using queryset attribute will lead error on testing, use get_queryset method intead
    # queryset = ProductSKU.objects.get_trending_products().order_by('?')[:8]

    def get_queryset(self):
        try:
            queryset = ProductSKU.objects.get_trending_products().\
                order_by('?')[:8]
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
        queryset = ProductSKU.objects.get_queryset()

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
        conn = get_redis_connection('cart')
        wishlisted = conn.smembers(f'wish_{user.id}')
        wishlisted = [int(i) for i in wishlisted]
        for product in queryset:
            if product.id in wishlisted:
                product.wishlist = True

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: duplicate with get_queryset, figure out a better solution to reduce duplicate query
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            context['category'] = category

        # NOTE:when query set is paginated, use paginator to return total results count,
        # otherwise use queryset count, including 0 item case
        try:
            context['count'] = context['paginator'].count
        except AttributeError:
            context['count'] = context['object_list'].count()

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
        return super().get_queryset().prefetch_related('order_products__review')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context['images'] = product.images.all()
        context['related_products'] = ProductSKU.objects.get_related_products(
            product)[:4]

        context['reviews'] = [
            op.review for op in product.orderproducts.all() if op.is_reviewed]
        return context
