from domain.shared.entity import Entity


class ProductCollection(Entity):
    def __init__(self, name):
        self.name = name
        self.master = None
        self.products = []

    def __len__(self):
        return len(self.products)

    def __contains__(self, item):
        return self.products.count(item)