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

    def add_product(self, sku):
        if sku in self:
           return False

        self.products.append(sku)
        return True

    def remove_product(self, sku):
        if sku not in self:
            return False

        self.products.remove(sku)
        return True