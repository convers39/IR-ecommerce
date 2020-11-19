from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls', namespace='shop')),
    path('account/', include('account.urls', namespace='account')),
    path('order/', include('order.urls', namespace='order')),
    path('cart/', include('cart.urls', namespace='cart')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls)), ]\
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
