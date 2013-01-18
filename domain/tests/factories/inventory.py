import factory

from domain.model.inventory.inventory_items import InventoryItem

class InventoryItemFactory(factory.Factory):
    FACTORY_FOR = InventoryItem
    sku = factory.Sequence(lambda n: 'PROD%03d'% n, type=int)
