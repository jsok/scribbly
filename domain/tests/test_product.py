from unittest import TestCase, skip

from factories.product import ProductFactory

class ProductTestCase(TestCase):

    def test_product_creation(self):
        p = ProductFactory.build()

        self.assertIsNotNone(p.sku, "Product was created without an SKU")