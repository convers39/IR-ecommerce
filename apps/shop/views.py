from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django.views.generic import ListView, View, DetailView
from django.views.generic.detail import SingleObjectMixin
from .models import ProductSKU, ProductSPU, Category, Origin, Image

# Create your views here.


class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')


class ProductSearchView(ListView):
    model = ProductSKU
    template_name = 'shop/product-search.html'
    paginate_by = 2

    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', None)
        if not search_term:
            messages.warning(
                request, 'Empty search content, please enter again.')
            return redirect(reverse('shop:product-list'))

        products = ProductSKU.objects.filter(name__icontains=search_term)
        count = products.count()

        return render(request, self.template_name, {'products': products, 'count': count})


class ProductListView(ListView):
    model = ProductSKU
    context_object_name = 'products'
    template_name = 'shop/product-list.html'
    queryset = ProductSKU.objects.all()
    paginate_by = 2

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.values('id', 'name', 'slug')
        # context["origin"] = Origin
        context["count"] = self.queryset.count()
        return context

    def get_queryset(self):
        return super().get_queryset()


class CategoryListView(SingleObjectMixin, ListView):
    model = ProductSKU
    paginate_by = 2
    template_name = 'shop/product-category.html'
    slug_url_kwarg = 'category_slug'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Category.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.object
        context['count'] = self.get_queryset().count()
        context['products'] = self.object_list
        return context

    def get_queryset(self):
        return self.object.sku.all()


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
