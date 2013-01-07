from domain.shared.entity import Entity

class Product(Entity):
    def __init__(self, sku, name, price, price_category=None):
        self.sku = sku
        self.name = name
        self.price = price
        self.price_category = price_category if price_category else None
        self.collections = []

    def join_collection(self, collection):
        from domain.model.product.product_collection import ProductCollection
        if isinstance(collection, ProductCollection):
            self.collections.append(collection)

    def leave_collection(self, collection):
        from domain.model.product.product_collection import ProductCollection
        if isinstance(collection, ProductCollection):
            self.collections.remove(collection)
