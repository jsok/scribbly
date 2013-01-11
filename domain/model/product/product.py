from datetime import datetime

from domain.shared.entity import Entity

from domain.model.product.price_value import PriceValue
from domain.model.product.product_collection import ProductCollection

class Product(Entity):
    def __init__(self, sku, name, price, price_category=None):
        self.sku = sku
        self.name = name
        self.collections = []

        if not isinstance(price, PriceValue):
            raise TypeError()

        self.price_history = self.PriceHistory()
        self.set_price(price)
        self.price_category = price_category if price_category else None

    def set_price(self, price):
        if not isinstance(price, PriceValue):
            raise TypeError()

        self.price_history.append(price)

    def get_price(self, date):
        price = self.price_history.at_date(date)
        return price.price if price else None

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

    class PriceHistory(object):
        '''
        Collection object for price values.
        '''

        def __init__(self):
            self.history = []

        def append(self, price):
            self.history.append(price)
            self.history.sort(reverse=True)

        def at_date(self, date):
            # Get the first PriceValue in the history whose date is lte to the provided one
            return next((price for price in self.history if price.date <= date), None)