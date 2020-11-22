import factory
from factory.django import DjangoModelFactory
from taggit.managers import TaggableManager
from taggit.models import TaggedItem

from shop.models import ProductSPU, ProductSKU, Origin, Category, Image


class CategoryFacotry(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: 'awesome category %d' % n)
    desc = factory.Faker('sentence')


class OriginFacotry(DjangoModelFactory):
    class Meta:
        model = Origin

    name = factory.Faker('city')
    desc = factory.Faker('sentence')


class SpuFacotry(DjangoModelFactory):
    class Meta:
        model = ProductSPU

    name = factory.Faker('company')
    desc = factory.Faker('sentence')


class TagsFactory(DjangoModelFactory):
    class Meta:
        model = TaggedItem


class SkuFactory(DjangoModelFactory):
    class Meta:
        model = ProductSKU

    name = factory.Sequence(lambda n: 'awesome item %d' % n)
    summary = factory.Faker('sentence')
    unit = 1
    price = 500
    brand = factory.Faker('company')
    # tags = ProductSKU.tags.add('bug')
    # tags = ['buff']
    category = factory.SubFactory(CategoryFacotry)
    origin = factory.SubFactory(OriginFacotry)
    spu = factory.SubFactory(SpuFacotry)

    # @factory.post_generation
    # def tags(self, create, extracted, **kwargs):
    #     if not create:
    #         # Simple build, do nothing.
    #         return

    #     if extracted:
    #         # A list of groups were passed in, use them
    #         for tags in extracted:
    #             self.tags.add(tags)


class ImageFacotry(DjangoModelFactory):
    class Meta:
        model = Image
