import operator

from domain.shared.entity import  Entity

class PackingList(Entity):
    id = None
    date = None
    packer = None
    items = None

    def __init__(self, id, date, packer=None, items=None):
        self.id = id
        self.date = date
        self.packer = packer if packer else None
        self.items = items if items else {}

    def add_item(self, sku, order_id, quantity):
        item = self.items.get(sku, self.Item(sku))
        item.add_entry(order_id, quantity)
        self.items.update({sku: item})

    def find_item(self, sku):
        return self.items.get(sku)

    class Item(object):
        sku = None
        order_entries = None

        def __init__(self, sku):
            self.sku = sku
            self.order_entries = []

        def add_entry(self, order_id, quantity):
            self.order_entries.append((order_id, quantity))

        def total_items(self):
            return reduce(operator.add, [qty for _, qty in self.order_entries], 0)