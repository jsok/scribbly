import factory

from domain.model.product import product, product_collection, taxon

class ProductFactory(factory.Factory):
    FACTORY_FOR = product.Product

    sku = factory.Sequence(lambda n: 'PROD%03d'% n, type=int)
    name = factory.Sequence(lambda n: 'Product %03d'% n, type=int)
    price = 0.00

class ProductCollectionFactory(factory.Factory):
    FACTORY_FOR = product_collection.ProductCollection

    name = "Default Product Collection"

class TaxonFactory(factory.Factory):
    FACTORY_FOR = taxon.Taxon

    name = "Taxon"