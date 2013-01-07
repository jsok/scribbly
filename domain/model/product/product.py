from domain.shared.entity import Entity

class Product(Entity):
    sku = None
    name = None
    price = None
    price_category = None

    def __init__(self, sku, name, price, price_category=None):
        self.sku = sku
        self.name = name
        self.price = price
        self.price_category = price_category if price_category else None