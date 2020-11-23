from django.contrib import admin
from .models import ProductSPU, ProductSKU, Origin, HomeBanner, Category, Image
from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter


class ImageInline(admin.TabularInline):
    model = Image
    exclude = ('is_deleted',)
    max_num = 3


@admin.register(ProductSKU)
class SKUAdmin(admin.ModelAdmin):
    ordering = ('name', 'category',)
    list_display = ('name', 'spu', 'category',
                    'origin', 'stock', 'price', 'sales')
    search_fields = ('name', 'summary', 'detail',)
    list_filter = ('status', 'spu', 'category', 'origin',)

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
    list_display = ('tree_actions', 'indented_title',
                    'related_products_count', 'related_products_cumulative_count')
    list_display_links = ('indented_title',)
    # list_filter = (('Category', TreeRelatedFieldListFilter),)

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


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)
