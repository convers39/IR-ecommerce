from django.contrib import admin
from django import forms
from easy_select2.utils import apply_select2

from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter
from .models import ProductSPU, ProductSKU, Origin, HomeBanner, Category, Image

# SKUForm = select2_modelform(ProductSKU, attrs={'width': '50%'})


class SKUForm(forms.ModelForm):
    class Meta:
        widgets = {
            'spu': apply_select2(forms.Select),
            'category': apply_select2(forms.Select),
            'origin': apply_select2(forms.Select),
        }


class ImageInline(admin.TabularInline):
    model = Image
    exclude = ('is_deleted',)
    max_num = 3


@admin.register(ProductSKU)
class SKUAdmin(admin.ModelAdmin):
    form = SKUForm
    model = ProductSKU
    ordering = ('name', 'category',)
    list_display = ('id', 'name', 'spu', 'category',
                    'origin', 'stock', 'price', 'sales')
    search_fields = ('id', 'name', 'summary', 'detail',)
    list_filter = ('status', 'spu', 'origin',
                   ('category_id', TreeRelatedFieldListFilter),)
    autocomplete_fields = ('spu_id', 'category_id', 'origin_id')
    list_editable = ('stock', 'price', )
    list_select_related = ('category', 'spu', 'origin',)
    list_per_page = 10
    list_max_show_all = 50
    save_as = True
    fieldsets = (
        ('Basic Information', {
            "fields": (
                'name', 'slug', 'spu', 'unit', 'price', 'stock',
            ),
        }),
        ('Description', {
            'fields': (
                'category', 'summary', 'cover_img', 'detail', 'brand', 'origin', 'tags'
            )
        }),
        ('Sales Data', {
            'fields': (
                'status', 'sales',
            )
        })
    )
    inlines = [ImageInline]


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "name"
    list_display = ('id', 'tree_actions', 'indented_title',
                    'related_products_count', 'related_products_cumulative_count')
    list_display_links = ('indented_title', )
    list_display = ('indented_title', 'name', )
    list_editable = ('name',)
    search_fields = ('name',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Add cumulative product count
        qs = Category.objects.add_related_count(
            qs, ProductSKU, 'category', 'products_cumulative_count', cumulative=True)

        # Add non cumulative product count
        qs = Category.objects.add_related_count(
            qs, ProductSKU, 'category', 'products_count', cumulative=False)
        return qs

    def related_products_count(self, instance):
        return instance.products_count
    related_products_count.short_description = 'Related products (for this specific category)'

    def related_products_cumulative_count(self, instance):
        return instance.products_cumulative_count
    related_products_cumulative_count.short_description = 'Related products (in tree)'


@admin.register(HomeBanner)
class HomeBannerAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)


@admin.register(ProductSPU)
class SPUAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)
    search_fields = ('name',)
    # list_editable = ('name',)
    list_display = ('name',)
    list_display_links = ('name',)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)
    list_editable = ('name',)
    list_display = ('name', 'image')
    list_display_links = None
    list_select_related = ('sku',)


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)
    search_fields = ('name',)
    list_editable = ('name',)
    list_display = ('name',)
    list_display_links = None
