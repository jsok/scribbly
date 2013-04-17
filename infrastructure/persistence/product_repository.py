from infrastructure.persistence.repository import Repository
from domain.model.product.product import Product


class ProductRepository(Repository):
    def __init__(self, session):
        super(ProductRepository, self).__init__(session)

    def find(self, sku):
        query = self.session.query(Product).filter(Product.sku == sku)

        return super(ProductRepository, self).find(query)

    def store(self, product_entity):
        self.session.add(product_entity)
        self.session.commit()