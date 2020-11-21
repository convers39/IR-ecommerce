from django.test import TestCase, Client, override_settings
from django.urls import resolve, reverse
from django.conf import settings
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import InMemoryUploadedFile

from PIL import Image
import tempfile

from .factory import SkuFactory, CategoryFacotry, OriginFacotry, SpuFacotry

# TODO: finish view test


def get_temporary_image(temp_file):
    size = (200, 200)
    color = (255, 0, 0, 0)
    image = Image.new("RGB", size, color)
    image.save(temp_file, 'jpeg')
    return temp_file


class TestShopListView(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.category = CategoryFacotry()
        for _ in range(4):
            dummy = SkuFactory()
            temp_file = tempfile.NamedTemporaryFile()
            dummy.category = cls.category
            dummy.cover_img = get_temporary_image(temp_file.name)
            dummy.save()

    def test_view_url_reverse(self):
        self.assertEqual(reverse('shop:product-list'), '/shop/')
        self.assertEqual(reverse('shop:category-list', kwargs={
                         'category_slug': self.category.slug}), f'/shop/{self.category.slug}/')
        self.assertEqual(reverse('shop:index'), '/')

    # @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_shop_list_view_GET(self):
        res = self.client.get(reverse('shop:product-list'))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['is_paginated'])
        self.assertTemplateUsed(res, 'shop/product-list.html')

    def test_shop_list_category_view_GET(self):
        res = self.client.get(f'/shop/{self.category.slug}/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['is_paginated'])
        self.assertTemplateUsed(res, 'shop/product-list.html')

    def test_shop_list_view_search_GET(self):
        res = self.client.get(reverse('shop:product-list')+'?q=awesome')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['is_paginated'])
        self.assertTemplateUsed(res, 'shop/product-list.html')

    def test_shop_list_view_sort_GET(self):
        res = self.client.get(reverse('shop:product-list')+'?sorting=sales')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['is_paginated'])
        self.assertTemplateUsed(res, 'shop/product-list.html')


class TestShopDetailView(TestCase):
    pass


class TestShopIndexView(TestCase):
    pass
