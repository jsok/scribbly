import factory

from domain.model.product import product

class ProductFactory(factory.Factory):
    FACTORY_FOR = product.Product

    sku = factory.Sequence(lambda n: 'PROD%03d'% n, type=int)
    name = factory.Sequence(lambda n: 'Product %03d'% n, type=int)
    price = 0.00
