import datetime
import factory

from domain.model.product import product, product_collection
from domain.model.product.price_value import PriceValue

class ProductFactory(factory.Factory):
    FACTORY_FOR = product.Product

    sku = factory.Sequence(lambda n: 'PROD%03d'% n, type=int)
    name = factory.Sequence(lambda n: 'Product %03d'% n, type=int)
    price = PriceValue(100.00, datetime.datetime.now())

class PriceValueFactory(factory.Factory):
    FACTORY_FOR = PriceValue

    price = 100.00
    date = datetime.datetime.now()

class ProductCollectionFactory(factory.Factory):
    FACTORY_FOR = product_collection.ProductCollection

    name = "Default Product Collection"