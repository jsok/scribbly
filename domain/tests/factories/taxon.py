import factory
from domain.model.taxon import taxon

class TaxonFactory(factory.Factory):
    FACTORY_FOR = taxon.Taxon

    name = "Taxon"