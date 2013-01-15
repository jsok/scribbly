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