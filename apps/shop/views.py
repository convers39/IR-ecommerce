from django.core import paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.template import context
from django.urls import reverse
from django.views.generic import ListView, View, DetailView
from .models import ProductSKU, ProductSPU, Category, Origin, Image

# Create your views here.


class IndexView(View):
    def get(self, request):
        context = {}
        categories = Category.objects.all()
        context['categories'] = categories
        return render(request, 'index.html', context)


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
        # check if user input a search text
        search_term = self.request.GET.get('search')
        if search_term:
            queryset = ProductSKU.objects.search(search_term)
        # check if search by category
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)
        # check if search by tag
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__name__in=[tag])
        if not queryset:
            messages.error(self.request, 'No results found!')
        queryset = queryset.order_by(self.get_ordering())
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = Category.objects.get(slug=category_slug)
            context['category'] = category
        # when query set is paginated, use paginator to return total results count,
        # otherwise use queryset count, including 0 item case
        try:
            context['count'] = context['paginator'].count
        except AttributeError:
            context['count'] = context['object_list'].count()

        context["categories"] = Category.objects.all()
        return context


class ProductDetailView(DetailView):
    model = ProductSKU
    context_object_name = 'product'
    template_name = 'shop/product-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = self.object.images.all()
        context['related_products'] = ProductSKU.objects.get_same_category_products(
            self.object)[:4]
        return context

    def render_to_response(self, context):
        return super().render_to_response(context)
