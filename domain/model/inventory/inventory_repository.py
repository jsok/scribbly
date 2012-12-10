from domain.shared.repository import Repository

from domain.model.inventory.inventory_items import InventoryItem

class InventoryRepository(Repository):

    def add_to_inventory(self, product, warehouse):
        item = InventoryItem(on_hand=0, warehouse=warehouse.id)
        self.create(item)

    def find_by_sku(self, SKU):
        """
        Find an inventory item by its SKU.
        Returns an InventoryItem.
        """
        item = self.find(SKU)
        item.repository = self
        return item

    def find_backorders_by_sku(self, sku):
        return NotImplementedError()
