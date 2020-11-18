from django.shortcuts import render
from django.views.generic import ListView, View, DetailView
from django.views.generic.detail import SingleObjectMixin
from .models import ProductSKU, ProductSPU, Category, Origin, Image

# Create your views here.


class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')


class ProductListView(ListView):
    model = ProductSKU
    context_object_name = 'products'
    template_name = 'product-list.html'
    queryset = ProductSKU.objects.all()
    paginate_by = 2

    def get_context_data(self, **kwargs):
        count = self.queryset.count()
        context = super().get_context_data(**kwargs)
        context["categories"] = Category
        context["origin"] = Origin
        context["count"] = count
        return context

    def get_queryset(self):
        return super().get_queryset()


class CategoryListView(SingleObjectMixin, ListView):
    model = ProductSKU
    paginate_by = 2
    template_name = 'category-list.html'
    slug_url_kwarg = 'category_slug'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Category.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.object
        context['count'] = self.get_queryset().count()
        return context

    def get_queryset(self):
        return self.object.sku.all()


class ProductDetailView(DetailView):
    model = ProductSKU
    context_object_name = 'product'
    template_name = 'product-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["spu"] = ProductSPU
        context['images'] = self.object.images.all()
        context['related_products'] = ProductSKU.objects.get_same_category_products(
            self.object)[:4]
        return context

    def render_to_response(self, context):
        return super().render_to_response(context)
