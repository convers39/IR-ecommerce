from django.db.models.signals import post_save
import factory
from factory.django import DjangoModelFactory
from taggit.managers import TaggableManager
from taggit.models import TaggedItem

from shop.models import ProductSPU, ProductSKU, Origin, Category, Image, HomeBanner


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: 'awesome category %d' % n)
    desc = factory.Faker('sentence')
    image = factory.django.ImageField()


class OriginFactory(DjangoModelFactory):
    class Meta:
        model = Origin

    name = factory.Faker('city')
    desc = factory.Faker('sentence')


class SpuFactory(DjangoModelFactory):
    class Meta:
        model = ProductSPU

    name = factory.Faker('company')
    desc = factory.Faker('sentence')


class TagsFactory(DjangoModelFactory):
    class Meta:
        model = TaggedItem


@factory.django.mute_signals(post_save)
class SkuFactory(DjangoModelFactory):
    class Meta:
        model = ProductSKU

    name = factory.Sequence(lambda n: 'awesome item %d' % n)
    summary = factory.Faker('sentence')
    unit = 1
    price = 500
    brand = factory.Faker('company')
    cover_img = factory.django.ImageField()
    # tags = ProductSKU.tags.add('bug')
    # tags = ['buff']
    category = factory.SubFactory(CategoryFactory)
    origin = factory.SubFactory(OriginFactory)
    spu = factory.SubFactory(SpuFactory)

    # @factory.post_generation
    # def tags(self, create, extracted, **kwargs):
    #     if not create:
    #         # Simple build, do nothing.
    #         return

    #     if extracted:
    #         # A list of groups were passed in, use them
    #         for tags in extracted:
    #             self.tags.add(tags)


class ImageFactory(DjangoModelFactory):
    class Meta:
        model = Image

    name = factory.Faker('last_name')
    image = factory.django.ImageField()
    sku = factory.SubFactory(SkuFactory)


class BannerFactory(DjangoModelFactory):
    class Meta:
        model = HomeBanner

    index = factory.Sequence(int)
    image = factory.django.ImageField()
    sku = factory.SubFactory(SkuFactory)
