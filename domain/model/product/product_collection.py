from domain.shared.entity import Entity

from domain.model.product.product import Product

class ProductCollection(Entity):
    def __init__(self, name, master=None):
        self.name = name
        self.master = master if isinstance(master, Product) else None
        self.products = []

    def __len__(self):
        return len(self.products)

    def add_product(self, product):
        if isinstance(product, Product):
            self.products.append(product)
            product.join_collection(self)

    def remove_product(self, sku):
        for product in self.products:
            if product.sku == sku:
                self.products.remove(product)
                product.leave_collection(self)