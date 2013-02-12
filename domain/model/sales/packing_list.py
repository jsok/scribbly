from domain.shared.entity import Entity


class PackingList(Entity):
    """
    A document which is used to help order packing staff find and collect all required items for a delivery.
    """

    def __init__(self, packinglist_id, date, packer=None):
        self.packinglist_id = packinglist_id
        self.date = date
        self.packer = packer if packer else None
        self.line_items = {}
        self.packed = False

    def add_item(self, sku, quantity, warehouse, order_id):
        entries = self.line_items.get(sku, [])
        entries.append({"quantity": quantity, "warehouse": warehouse, "order_id": order_id})
        self.line_items.update({sku: entries})

    def find_item(self, sku):
        return self.line_items.get(sku, None)

    def list_orders(self):
        order_ids = set()
        for item in self.line_items.itervalues():
            map(lambda order_id: order_ids.add(order_id), [entry["order_id"] for entry in item])
        return order_ids

    def list_skus(self):
        return self.line_items.keys()
