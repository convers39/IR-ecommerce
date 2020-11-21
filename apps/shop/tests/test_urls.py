from django.test import SimpleTestCase
from django.urls import reverse, resolve

from shop.views import ProductListView, ProductDetailView, IndexView


class TestShopUrls(SimpleTestCase):

    def test_index_url(self):
        url = reverse('shop:index')
        self.assertEqual(resolve(url).func.__name__,
                         IndexView.as_view().__name__)

    def test_product_list_url(self):
        url = reverse('shop:product-list')
        self.assertEqual(resolve(url).func.__name__,
                         ProductListView.as_view().__name__)

    def test_category_list_url(self):
        url = reverse('shop:category-list',
                      kwargs={'category_slug': 'japanese-awesome-stuff'})
        self.assertEqual(resolve(url).func.__name__,
                         ProductListView.as_view().__name__)

    def test_product_detail_url(self):
        url = reverse('shop:product-detail',
                      kwargs={'pk': 1, 'slug': 'awesome-item'})
        self.assertEqual(resolve(url).func.__name__,
                         ProductDetailView.as_view().__name__)
