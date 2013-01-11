from unittest import TestCase, skip

from factories.product import ProductFactory, ProductCollectionFactory, TaxonFactory

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

class TaxonTestCase(TestCase):

    def test_single_root_taxon(self):
        taxon = TaxonFactory.build(name="Root")

        self.assertEquals("/", taxon.path_basename(), "Taxon base path was generated incorrectly")
        self.assertEquals("/Root", taxon.path(), "Taxon path was generated incorrectly")

    def test_multiple_taxons(self):
        root = TaxonFactory.build(name="Root")
        middle = TaxonFactory.build(name="Middle", parent=root)
        child1 = TaxonFactory.build(name="Child 1", parent=middle)
        child2 = TaxonFactory.build(name="Child 2", parent=middle)

        self.assertEquals("/", root.path_basename(), "Taxon base path was generated incorrectly")
        self.assertEquals("/Root", root.path(), "Taxon path was generated incorrectly")

        self.assertEquals("/Root", middle.path_basename(), "Taxon base path was generated incorrectly")
        self.assertEquals("/Root/Middle", middle.path(), "Taxon path was generated incorrectly")

        self.assertEquals("/Root/Middle", child1.path_basename(), "Child base path was generated incorrectly")
        self.assertEquals("/Root/Middle/Child 1", child1.path(), "Child path was generated incorrectly")

        self.assertEquals("/Root/Middle", child2.path_basename(), "Child base path was generated incorrectly")
        self.assertEquals("/Root/Middle/Child 2", child2.path(), "Child path was generated incorrectly")
