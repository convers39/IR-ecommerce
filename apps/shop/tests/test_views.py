from django.core.paginator import InvalidPage
from django.test import TestCase, Client, override_settings
from django.urls import resolve, reverse
from django.contrib.messages import get_messages


from PIL import Image
import tempfile

from shop.views import ProductListView
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
        for _ in range(10):
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
    def test_shop_list_view_show_items(self):
        res = self.client.get(reverse('shop:product-list'))
        total_count = int(res.context['paginator'].count)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(total_count, 10)
        self.assertTemplateUsed(res, 'shop/product-list.html')
        self.assertEqual(res.resolver_match.func.__name__,
                         ProductListView.as_view().__name__)

    def test_shop_list_view_pagination(self):
        res = self.client.get(reverse('shop:product-list'))
        paginator = res.context['paginator']
        object_per_page = res.context['object_list'].count()
        paginate_by = paginator.per_page
        orphan = paginator.orphans
        last_page = paginator.get_page(paginator.num_pages)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['is_paginated'])
        self.assertEqual(object_per_page, paginate_by)
        self.assertEqual(orphan+paginate_by, len(last_page))

    def test_bad_page_request(self):
        res = self.client.get(reverse('shop:product-list')+'?page=100')
        self.assertRaises(InvalidPage)
        self.assertEqual(res.status_code, 404)

    def test_category_list_view(self):
        res = self.client.get(f'/shop/{self.category.slug}/')
        item = res.context['object_list'][0]
        self.assertEqual(res.status_code, 200)
        self.assertEqual(item.category, self.category)
        self.assertTrue(res.context['is_paginated'])
        self.assertTemplateUsed(res, 'shop/product-list.html')
        self.assertEqual(res.resolver_match.func.__name__,
                         ProductListView.as_view().__name__)

    def test_category_list_view_404(self):
        res = self.client.get('/shop/random_slug/')
        self.assertEqual(res.status_code, 404)

    def test_shop_list_view_search(self):
        res = self.client.get(reverse('shop:product-list')+'?search=awesome')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['is_paginated'])
        self.assertTemplateUsed(res, 'shop/product-list.html')

    def test_shop_list_no_result_found(self):
        res = self.client.get(
            reverse('shop:product-list')+'?search=randomstuff')
        items = res.context['object_list']
        msg = list(get_messages(res.wsgi_request))
        self.assertEqual(res.status_code, 200)
        self.assertFalse(items)
        self.assertEqual(str(msg[0]), 'No results found!')
        self.assertTemplateUsed(res, 'shop/product-list.html')

    def test_shop_list_view_sort(self):
        res = self.client.get(reverse('shop:product-list')+'?sorting=sales')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['is_paginated'])
        self.assertTemplateUsed(res, 'shop/product-list.html')

    def test_shop_list_view_invalid_sort(self):
        res = self.client.get(
            reverse('shop:product-list')+'?sorting=invalidsort')
        items = res.context['object_list']
        msg = list(get_messages(res.wsgi_request))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(items)
        self.assertEqual(str(msg[0]), 'Sorted by default (latest).')
        self.assertTrue(res.context['is_paginated'])
        self.assertTemplateUsed(res, 'shop/product-list.html')


class TestShopDetailView(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.sku = SkuFactory()
        # cls.sku.tags.add('awesome')
        temp_file = tempfile.NamedTemporaryFile()
        cls.sku.cover_img = get_temporary_image(temp_file.name)
        for i in range(3):
            temp = tempfile.NamedTemporaryFile()
            cls.sku.images.create(
                name=f'image-{i}', image=get_temporary_image(temp.name))

    def test_detail_view_show_item(self):
        res = self.client.get(reverse(
            'shop:product-detail', kwargs={'pk': self.sku.id, 'slug': self.sku.slug}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'shop/product-detail.html')

    def test_show_related_item(self):
        for _ in range(3):
            new_sku = SkuFactory()
            temp_file = tempfile.NamedTemporaryFile()
            new_sku.cover_img = get_temporary_image(temp_file.name)
            new_sku.category = self.sku.category
            new_sku.save()
        res = self.client.get(reverse(
            'shop:product-detail', kwargs={'pk': self.sku.id, 'slug': self.sku.slug}))
        related_items = res.context['related_products']
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(related_items), 3)
        self.assertTemplateUsed(res, 'shop/product-detail.html')

    def test_show_item_images(self):
        res = self.client.get(reverse(
            'shop:product-detail', kwargs={'pk': self.sku.id, 'slug': self.sku.slug}))
        images = res.context['images']
        self.assertEqual(len(images), 3)
        self.assertCountEqual(images, self.sku.images.all())

    def test_item_does_not_exist(self):
        res = self.client.get(reverse(
            'shop:product-detail', kwargs={'pk': self.sku.id+100, 'slug': self.sku.slug+'random'}))
        self.assertEqual(res.status_code, 404)

    # TODO: figure out how to test with taggit
    # def test_tags_search(self):
    #     new_sku = SkuFactory
    #     new_sku.tags.add('awesome')
    #     res = self.client.get(reverse('shop:product-list')+f'?tag=awesome')
    #     items = res.context['object_list']
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(len(items), 2)
    #     self.assertTemplateUsed(res, 'shop/product-list.html')


class TestShopIndexView(TestCase):
    pass
