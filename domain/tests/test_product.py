from unittest import TestCase, skip

from factories.product import ProductFactory, ProductCollectionFactory

class ProductTestCase(TestCase):

    def test_product_creation(self):
        p = ProductFactory.build()

        self.assertIsNotNone(p.sku, "Product was created without an SKU")

class ProductCollectionTestCase(TestCase):

    def test_product_collection_empty(self):
        collection = ProductCollectionFactory.build(name="Empty Collection")

        self.assertEquals(0, len(collection), "Collection is not empty")
        self.assertIsNone(collection.master, "Collection Master should not be set")

    def test_product_collection_empty_with_master(self):
        p = ProductFactory.build()
        collection = ProductCollectionFactory.build(name="Empty Collection", master=p)

        self.assertEquals(0, len(collection), "Collection is not empty")
        self.assertIsNotNone(collection.master, "Collection Master should be set")

    def test_product_collection_variant_group(self):
        products = [
            ProductFactory.build(sku="PROD000-A"),
            ProductFactory.build(sku="PROD000-B"),
            ProductFactory.build(sku="PROD000-C"),
        ]
        collection = ProductCollectionFactory.build(name="PROD000 Variants")
        map(lambda p: collection.add_product(p), products)

        self.assertEquals(3, len(collection), "Incorrect number of products in collection")
        self.assertIsNone(collection.master, "Collection master should not be set")

        for p in products:
            self.assertEquals(1, len(p.collections), "%s is not aware it's in a collection" % p.sku)

        collection.remove_product("PROD000-A")
        self.assertEquals(2, len(collection), "Incorrect number of products in collection")
        self.assertEquals(0, len(products[0].collections), "PROD000-A did not leave collection")

    def test_product_collection_replacement_group(self):
        master = ProductFactory.build(sku="PROD000")
        replacements = [
            ProductFactory.build(sku="REPLACEMENT-A"),
            ProductFactory.build(sku="REPLACEMENT-B"),
            ]
        collection = ProductCollectionFactory.build(name="PROD000 Variants", master=master)
        map(lambda p: collection.add_product(p), replacements)

        self.assertEquals(2, len(collection), "Incorrect number of products in collection")
        self.assertIsNotNone(collection.master, "Collection master should not be set")

        for p in replacements:
            self.assertEquals(1, len(p.collections), "%s is not aware it's in a collection" % p.sku)
