import factory
from factory.django import DjangoModelFactory

# TODO: find method to mock image data

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


class SkuFactory(DjangoModelFactory):
    class Meta:
        model = ProductSKU

    name = factory.Sequence(lambda n: 'awesome item %d' % n)
    summary = factory.Faker('sentence')
    unit = 1
    price = 500
    brand = factory.Faker('company')

    category = factory.SubFactory(CategoryFacotry)
    origin = factory.SubFactory(OriginFacotry)
    spu = factory.SubFactory(SpuFacotry)


class ImageFacotry(DjangoModelFactory):
    class Meta:
        model = Image
