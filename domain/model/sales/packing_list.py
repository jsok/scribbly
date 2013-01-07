import operator

from domain.shared.entity import  Entity
from domain.model.sales.line_item import LineItem

class PackingList(Entity):
    def __init__(self, id, date, packer=None, items=None):
        self.id = id
        self.date = date
        self.packer = packer if packer else None
        self.line_items = items if items else {}

    def add_item(self, sku, quantity, order_id):
        item = self.line_items.get(sku, self.PackingListItem(sku))
        item.add_entry(order_id, quantity)
        self.line_items.update({sku: item})

    def find_item(self, sku):
        return self.line_items.get(sku)

    def allocate_item(self, sku, quantity):
        item = self.find_item(sku)
        if item:
            item.allocated = quantity

    class PackingListItem(LineItem):
        def __init__(self, sku):
            self.sku = sku
            self.allocated = 0
            self.order_entries = []

        def add_entry(self, order_id, quantity):
            self.order_entries.append((order_id, quantity))

        @property
        def quantity(self):
            return reduce(operator.add, [qty for _, qty in self.order_entries], 0)
