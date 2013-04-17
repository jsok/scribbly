from datetime import datetime

from domain.shared.entity import Entity
from domain.shared.historical_value import HistoricalValueCollection

from domain.model.product.price_value import PriceValue
from domain.model.product.product_collection import ProductCollection
from domain.model.product.product_flag import ProductFlag


class Product(Entity):
    def __init__(self, sku, name, price, price_category=None):
        self.sku = sku
        self.name = name
        self.collections = []
        self.flags = {}

        if not isinstance(price, PriceValue):
            raise TypeError()

        self.price_history = HistoricalValueCollection()
        self.set_price(price)
        self.price_category = price_category if price_category else None

    def set_price(self, price):
        if not isinstance(price, PriceValue):
            raise TypeError()

        self.price_history.append(price)

    def get_price(self, date=None):
        date = date if date else datetime.now()
        price = self.price_history[date]
        return price.value if price else None

    def get_prices_between(self, start, end):
        return map(lambda p: p.value, self.price_history[start:end])

    def set_as_master_of_collection(self, collection):
        if isinstance(collection, ProductCollection):
            collection.master = self.sku

    def join_collection(self, collection):
        if isinstance(collection, ProductCollection):
            self.collections.append(collection)
        else:
            collection = ProductCollection(collection)
            self.collections.append(collection)

    def leave_collection(self, collection):
        if isinstance(collection, ProductCollection):
            collection = collection.name

        for c in self.collections:
            if c.name == collection:
                self.collections.remove(c)

    def set_flag(self, name, enabled):
        if self.flags.get(name):
            self.flags[name].set_flag(enabled)
        else:
            self.flags[name] = ProductFlag(name, enabled)

    def get_flag(self, name):
        if self.flags.get(name):
            return self.flags.get(name).get_flag()
        else:
            return False