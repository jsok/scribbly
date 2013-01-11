from datetime import datetime

from domain.shared.entity import Entity
from domain.shared.historical_value import HistoricalValueCollection

from domain.model.product.price_value import PriceValue
from domain.model.product.product_collection import ProductCollection

class Product(Entity):
    def __init__(self, sku, name, price, price_category=None):
        self.sku = sku
        self.name = name
        self.collections = []

        if not isinstance(price, PriceValue):
            raise TypeError()

        self.price_history = HistoricalValueCollection()
        self.set_price(price)
        self.price_category = price_category if price_category else None

    def set_price(self, price):
        if not isinstance(price, PriceValue):
            raise TypeError()

        self.price_history.append(price)

    def get_price(self, date):
        price = self.price_history[date]
        return price.value if price else None

    def get_prices_between(self, start, end):
        return map(lambda p: p.value, self.price_history[start:end])

    def get_current_price(self):
        return self.get_price(datetime.now())

    def set_as_master_of_collection(self, collection):
        if isinstance(collection, ProductCollection):
            collection.master = self.sku

    def join_collection(self, collection):
        if isinstance(collection, ProductCollection):
            if collection.add_product(self.sku):
                self.collections.append(collection)

    def leave_collection(self, collection):
        if isinstance(collection, ProductCollection):
            if collection.remove_product(self.sku):
                self.collections.remove(collection)
