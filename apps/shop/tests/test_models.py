from django.test import TestCase
# from unittest import mock

from shop.models import ProductSKU, Category, ProductSPU, Origin
from .factory import SkuFactory, CategoryFacotry, SpuFacotry, OriginFacotry


class TestSkuModel(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.sku = SkuFactory()

    def test_create_sku(self):
        count = ProductSKU.objects.count()
        item = SkuFactory()
        self.assertIsInstance(item, ProductSKU)
        self.assertEqual(count+1, ProductSKU.objects.count())

    def test_str_representation(self):
        self.assertEqual(str(self.sku), self.sku.name)

    def test_meta_verbose_name(self):
        self.assertEqual(str(self.sku._meta.verbose_name), 'SKU')
        self.assertEqual(str(self.sku._meta.verbose_name_plural), 'SKU')

    def test_get_absolute_url(self):
        url = self.sku.get_absolute_url()
        self.assertEqual(url, f'/shop/{self.sku.id}/{self.sku.slug}/')

    def test_create_slug_on_save(self):
        new_sku = SkuFactory(name='awesome new item')
        self.assertEqual(new_sku.slug, 'awesome-new-item')

    # @mock.patch('shop.tasks.update_search_vector')
    # def test_search_vector_update_post_save(self, mocked_update_search_vector):
    #     new_sku = SkuFactory()
    #     self.assertEqual(mocked_update_search_vector.call_count, 1)
    #     new_sku.name = 'changed name'
    #     new_sku.save()
    #     self.assertEqual(mocked_update_search_vector.call_count, 2)

    def test_text_in_price(self):
        price = self.sku.price * (1+0.1)
        self.assertAlmostEqual(self.sku.tax_in_price, price)
        self.assertIsInstance(self.sku.tax_in_price, float)


class TestCategoryModel(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = CategoryFacotry()

    def test_create_category(self):
        count = Category.objects.count()
        for _ in range(3):
            c = CategoryFacotry()
            self.assertIsInstance(c, Category)
        self.assertEqual(count+3, Category.objects.count())

    def test_add_sku_to_category(self):
        sku_count = ProductSKU.objects.count()
        for _ in range(3):
            sku = SkuFactory()
            self.category.sku.add(sku)
            self.assertEqual(sku.category, self.category)
        self.assertEqual(self.category.sku.count(), 3)
        self.assertEqual(sku_count+3, ProductSKU.objects.count())

    def test_str_representation(self):
        self.assertEqual(str(self.category), self.category.name)

    def test_meta_verbose_name(self):
        self.assertEqual(str(self.category._meta.verbose_name), 'category')
        self.assertEqual(
            str(self.category._meta.verbose_name_plural), 'categories')

    def test_create_slug_on_save(self):
        new_category = CategoryFacotry(name='awesome new category')
        self.assertEqual(new_category.slug, 'awesome-new-category')

    def test_get_absolute_url(self):
        url = self.category.get_absolute_url()
        self.assertEqual(url, f'/shop/{self.category.slug}/')


class TestSpuModel(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.spu = SpuFacotry()

    def test_create_spu(self):
        count = ProductSPU.objects.count()
        for _ in range(3):
            p = SpuFacotry()
            self.assertIsInstance(p, ProductSPU)
        self.assertEqual(count+3, ProductSPU.objects.count())

    def test_str_representation(self):
        self.assertEqual(str(self.spu), self.spu.name)

    def test_add_sku_to_spu(self):
        sku_count = ProductSKU.objects.count()
        for _ in range(3):
            sku = SkuFactory()
            self.spu.sku.add(sku)
            self.assertEqual(sku.spu, self.spu)
        self.assertEqual(self.spu.sku.count(), 3)
        self.assertEqual(sku_count+3, ProductSKU.objects.count())

    def test_meta_verbose_name(self):
        self.assertEqual(str(self.spu._meta.verbose_name), 'SPU')
        self.assertEqual(
            str(self.spu._meta.verbose_name_plural), 'SPU')


class TestOriginModel(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.origin = OriginFacotry()

    def test_create_origin(self):
        count = ProductSPU.objects.count()
        for _ in range(3):
            p = SpuFacotry()
            self.assertIsInstance(p, ProductSPU)
        self.assertEqual(count+3, ProductSPU.objects.count())

    def test_str_representation(self):
        self.assertEqual(str(self.origin), self.origin.name)

    def test_add_sku_to_origin(self):
        sku_count = ProductSKU.objects.count()
        for _ in range(3):
            sku = SkuFactory()
            self.origin.sku.add(sku)
            self.assertEqual(sku.origin, self.origin)
        self.assertEqual(self.origin.sku.count(), 3)
        self.assertEqual(sku_count+3, ProductSKU.objects.count())
