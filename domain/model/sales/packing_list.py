import operator

from domain.shared.entity import  Entity

class PackingList(Entity):
    def __init__(self, id, date, packer=None, items=None):
        self.id = id
        self.date = date
        self.packer = packer if packer else None
        self.line_items = items if items else {}

    def request_item(self, sku, quantity, order_id):
        item = self.line_items.get(sku, self.PackingListItem(sku))
        item.request(order_id, quantity)
        self.line_items.update({sku: item})

    def find_item(self, sku):
        return self.line_items.get(sku)

    def allocate_item(self, sku, quantity, warehouse):
        item = self.find_item(sku)
        if item:
            item.allocate(warehouse, quantity)

    class PackingListItem(object):
        def __init__(self, sku):
            self.sku = sku
            self._allocated = []
            self._order_entries = []

        def request(self, order_id, quantity):
            self._order_entries.append((order_id, quantity))

        def allocate(self, warehouse, quantity):
            self._allocated.append((warehouse, quantity))

        @property
        def quantity_requested(self):
            return reduce(operator.add, [qty for _, qty in self._order_entries], 0)

        @property
        def quantity_allocated(self):
            return reduce(operator.add, [qty for _, qty in self._allocated], 0)