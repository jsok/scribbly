from unittest import TestCase
from domain.tests.factories.taxon import TaxonFactory

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

    def test_taxon_with_products(self):
        taxon = TaxonFactory.build(name="Root")
        child = TaxonFactory.build(name="Child", parent=taxon)

        taxon.add_product("PROD000")
        taxon.add_product("PROD001")

        child.add_product("PROD000")

        self.assertEquals(2, len(taxon.products), "Incorrect number of products in root taxon")
        self.assertEquals(1, len(child.products), "Incorrect nunber of products in child taxon")

        child.remove_product("PRODFAKE")
        self.assertEquals(1, len(child.products), "Non-existent product removed other product from child taxon")

        child.remove_product("PROD000")
        self.assertEquals(0, len(child.products), "Product not removed from child taxon")