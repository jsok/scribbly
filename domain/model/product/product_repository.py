from domain.model.product.product import Product as ProductEntity
from domain.shared.repository import Repository
from domain.pricing.models import ProductPriceCategory
from domain.product.models import Product as ProductModel, Product

class ProductRepository(Repository):
    def create(self, entity):
        model = self.to_model(entity)
        model.save()

    def find(self, sku):
        model = ProductModel.objects.get(sku=sku)
        return self.to_entity(model)

    def add_price_category(self, name):
        category = ProductPriceCategory(name=name)
        category.save()