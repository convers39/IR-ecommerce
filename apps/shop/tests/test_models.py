from apps.order.tests.factory import OrderProductFactory, ReviewFactory
from django.test import TestCase

import factory

from shop.models import ProductSKU, Category, ProductSPU, Origin, HomeBanner
from .factory import BannerFactory, SkuFactory, CategoryFactory, SpuFactory, OriginFactory


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

    def test_review_count(self):
        for _ in range(3):
            op = OrderProductFactory(product=self.sku)
            review = ReviewFactory(order_product=op)
        self.assertEqual(self.sku.review_count, 3)

    def test_get_product_label_and_badge(self):
        sku1 = SkuFactory()
        sku2 = SkuFactory(sales=5)
        sku3 = SkuFactory(stock=0)
        self.assertEqual(sku1.get_product_label(), 'new')
        self.assertEqual(sku1.get_label_badge(), 'primary')
        self.assertEqual(sku2.get_product_label(), 'hot')
        self.assertEqual(sku2.get_label_badge(), 'danger')
        self.assertEqual(sku3.get_product_label(), 'sold')
        self.assertEqual(sku3.get_label_badge(), 'secondary')


class TestCategoryModel(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = CategoryFactory()

    def test_create_category(self):
        count = Category.objects.count()
        for _ in range(3):
            c = CategoryFactory()
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
        new_category = CategoryFactory(name='awesome new category')
        self.assertEqual(new_category.slug, 'awesome-new-category')

    def test_get_absolute_url(self):
        url = self.category.get_absolute_url()
        self.assertEqual(url, f'/shop/{self.category.slug}/')

    def test_get_full_category_name(self):
        cat1 = CategoryFactory(name='parent')
        cat2 = CategoryFactory(name='child', parent=cat1)
        cat2_full_name = cat2.get_full_category_name()
        self.assertTrue(cat2_full_name, 'parent/child')
        self.assertIn(cat2, cat1.children.all())


class TestSpuModel(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.spu = SpuFactory()

    def test_create_spu(self):
        count = ProductSPU.objects.count()
        for _ in range(3):
            p = SpuFactory()
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
        cls.origin = OriginFactory()

    def test_create_origin(self):
        count = ProductSPU.objects.count()
        for _ in range(3):
            p = SpuFactory()
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


class TestHomeBannerModel(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.banner = BannerFactory()

    def test_create_banner(self):
        count = HomeBanner.objects.count()
        banner = BannerFactory()
        self.assertIsInstance(banner, HomeBanner)
        self.assertEqual(count+1, HomeBanner.objects.count())

    def test_str_representation(self):
        self.assertEqual(str(self.banner), f'{self.banner.sku.name} banner')
