import datetime

from unittest import TestCase
from nose.tools import raises

from domain.tests.factories.product import ProductFactory, PriceValueFactory, ProductCollectionFactory

class ProductTestCase(TestCase):

    def test_product_creation(self):
        p = ProductFactory.build()

        self.assertIsNotNone(p.sku, "Product was created without an SKU")

class ProductPriceTestCase(TestCase):

    @raises(TypeError)
    def test_product_must_have_price(self):
        ProductFactory.build(price=None)

    @raises(TypeError)
    def test_product_price_non_value_type(self):
        ProductFactory.build(price=100.00)

    def test_product_current_price(self):
        p = ProductFactory.build(price=PriceValueFactory.build(price=100.00))

        self.assertEquals(100.00, p.get_current_price(), "Current price incorrect")

    def test_product_current_price_with_history(self):
        now = datetime.datetime.now()
        p = ProductFactory.build(price=PriceValueFactory.build(price=100.00, date=now))

        yesterday = now - datetime.timedelta(days=1)
        p.set_price(PriceValueFactory.build(price=150.00, date=yesterday))

        last_week = now - datetime.timedelta(weeks=1)
        p.set_price(PriceValueFactory.build(price=130.00, date=last_week))

        self.assertEquals(100.00, p.get_current_price(), "Current price incorrect")
        self.assertEquals(150.00, p.get_price(yesterday), "Yesterday price incorrect")
        self.assertEquals(150.00, p.get_price(now - datetime.timedelta(hours=1)), "Price an hour ago incorrect")
        self.assertEquals(130.00, p.get_price(now - datetime.timedelta(days=3)), "Price 3 days ago incorrect")

        # Update price again, delta should be small
        p.set_price(PriceValueFactory.build(price=90.00, date=datetime.datetime.now()))
        self.assertEquals(90.00, p.get_current_price(), "Updated current price incorrect")

        self.assertIsNone(p.get_price(now - datetime.timedelta(weeks=2)), "Price 2 weeks ago no undefined")

class ProductCollectionTestCase(TestCase):

    def test_product_collection_empty(self):
        collection = ProductCollectionFactory.build(name="Empty Collection")

        self.assertEquals(0, len(collection), "Collection is not empty")
        self.assertIsNone(collection.master, "Collection Master should not be set")

    def test_product_collection_empty_with_master(self):
        collection = ProductCollectionFactory.build(name="Empty Collection")
        p = ProductFactory.build()
        p.set_as_master_of_collection(collection)

        self.assertEquals(0, len(collection), "Collection is not empty")
        self.assertIsNotNone(collection.master, "Collection Master should be set")

    def test_product_collection_variant_group(self):
        products = [
            ProductFactory.build(sku="PROD000-A"),
            ProductFactory.build(sku="PROD000-B"),
            ProductFactory.build(sku="PROD000-C"),
        ]
        collection = ProductCollectionFactory.build(name="PROD000 Variants")
        map(lambda p: p.join_collection(collection), products)

        self.assertEquals(3, len(collection), "Incorrect number of products in collection")
        self.assertIsNone(collection.master, "Collection master should not be set")

        for p in products:
            self.assertEquals(1, len(p.collections), "%s is not aware it's in a collection" % p.sku)

        products[0].leave_collection(collection)
        self.assertEquals(2, len(collection), "Incorrect number of products in collection")
        self.assertEquals(0, len(products[0].collections), "PROD000-A did not leave collection")

    def test_product_collection_replacement_group(self):
        collection = ProductCollectionFactory.build(name="PROD000 Variants")
        master = ProductFactory.build(sku="PROD000")
        replacements = [
            ProductFactory.build(sku="REPLACEMENT-A"),
            ProductFactory.build(sku="REPLACEMENT-B"),
        ]

        master.set_as_master_of_collection(collection)
        map(lambda p: p.join_collection(collection), replacements)

        self.assertEquals(2, len(collection), "Incorrect number of products in collection")
        self.assertIsNotNone(collection.master, "Collection master should not be set")

        for p in replacements:
            self.assertEquals(1, len(p.collections), "%s is not aware it's in a collection" % p.sku)

class ProductFlagsTestCase(TestCase):

    def test_set_flag(self):
        p = ProductFactory.build()

        p.set_flag("Sale", True)
        p.set_flag("Hot", 1)

        self.assertTrue(p.get_flag("Sale"), "Sale flag was not set")
        self.assertTrue(p.get_flag("Hot"), "Hot flag was not set")
        self.assertFalse(p.get_flag("Deprecated"), "Deprecated flag should not be set")

        p.set_flag("Hot", False)
        self.assertFalse(p.get_flag("Hot"), "Hot flag was not cleared")