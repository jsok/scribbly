from nose_alembic_attrib import alembic_attr

from infrastructure.tests.persistence import PersistenceTestCase
from infrastructure.persistence.product_repository import ProductRepository

from domain.tests.factories.product import ProductFactory, PriceValueFactory, ProductCollectionFactory


class ProductRepositoryTestCase(PersistenceTestCase):
    def setUp(self):
        super(ProductRepositoryTestCase, self).setUp()
        self.repository = ProductRepository(self.session)

    @alembic_attr(minimum_revision="f5ea4e6bb80")
    def test_add_product(self):
        product = ProductFactory.build(sku='PROD001')
        product.set_flag("New", True)

        self.repository.store(product)

        product = self.repository.find('PROD001')
        self.assertIsNotNone(product, "Could not find product in repository")

        self.assertTrue(product.get_flag('New'), "Product flag was not set")

    @alembic_attr(minimum_revision="f5ea4e6bb80")
    def test_add_product_to_collection(self):
        products = [
            ProductFactory.build(sku="PROD000-A"),
            ProductFactory.build(sku="PROD000-B"),
            ProductFactory.build(sku="PROD000-C"),
        ]
        p_collection = ProductCollectionFactory.build(name="PROD000 Variants")
        a_collection = ProductCollectionFactory.build(name="A Variants")

        map(lambda p: p.join_collection(p_collection), products)
        products[0].join_collection(a_collection)
        map(lambda p: self.repository.store(p), products)

        product = self.repository.find('PROD000-B')
        self.assertIsNotNone(product, "Could not find product in repository")
        self.assertEquals(1, len(product.collections), "Product should belong to 1 collection")
        collection = product.collections[0]
        self.assertEquals(3, len(collection.products), "PROD000 Variants should contain 3 products")

        product = self.repository.find('PROD000-A')
        self.assertIsNotNone(product, "Could not find product in repository")
        self.assertEquals(2, len(product.collections), "Product should belong to 2 collections")

        product.leave_collection("PROD000 Variants")
        self.repository.store(product)

        product = self.repository.find('PROD000-A')
        self.assertIsNotNone(product, "Could not find product in repository")
        self.assertEquals(1, len(product.collections), "Product should belong to 1 collection")

        self.assertEquals(2, len(p_collection.products), "PROD000 Variants should only contain 2 products")
