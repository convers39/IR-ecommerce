from django.contrib import admin
from .models import ProductSPU, ProductSKU, Origin, HomeBanner, Category, Image


class ImageInline(admin.TabularInline):
    model = Image
    exclude = ('is_deleted',)
    max_num = 3


@admin.register(ProductSKU)
class SKUAdmin(admin.ModelAdmin):
    ordering = ('name', 'category',)
    list_display = ('name', 'spu', 'category',
                    'origin', 'stock', 'price', 'sales')
    search_fields = ('name', 'desc', 'detail',)
    list_filter = ('status', 'spu', 'category', 'origin',)

    fieldsets = (
        ('Basic Information', {
            "fields": (
                'name', 'slug', 'spu', 'unit', 'price', 'stock',
            ),
        }),
        ('Description', {
            'fields': (
                'category', 'desc', 'detail', 'brand', 'origin', 'tags'
            )
        }),
        ('Sales Data', {
            'fields': (
                'status', 'sales',
            )
        })
    )
    inlines = [ImageInline]


@admin.register(ProductSPU)
class SPUAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)


@admin.register(HomeBanner)
class HomeBannerAdmin(admin.ModelAdmin):
    readonly_fields = ('is_deleted',)
