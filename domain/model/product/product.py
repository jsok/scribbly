from domain.shared.entity import Entity

from domain.model.product.product_collection import ProductCollection

class Product(Entity):
    def __init__(self, sku, name, price, price_category=None):
        self.sku = sku
        self.name = name
        self.price = price
        self.price_category = price_category if price_category else None
        self.collections = []

    def set_as_master_of_collection(self, collection):
        if isinstance(collection, ProductCollection):
            collection.master = self.sku

    def join_collection(self, collection):
        if isinstance(collection, ProductCollection):
            if collection.add_product(self.sku):
                self.collections.append(collection)

    def leave_collection(self, collection):
        if not isinstance(collection, ProductCollection):
            return

        if collection.remove_product(self.sku):
            self.collections.remove(collection)
