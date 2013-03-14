from domain.shared.entity import Entity


class Delivery(Entity):
    def __init__(self, delivery_id, customer, date):
        self.delivery_id = delivery_id
        self.customer = customer
        self.date = date
        self.items = []
        self.invoice_ids = []

    def is_finalised(self):
        """
        A delivery is finalised once it has been invoiced
        """
        return len(self.invoice_ids) > 0

    def _find_item(self, sku, order_id):
        for item in self.items:
            if item["sku"] == sku and item["order_id"] == order_id:
                return item
        return None

    def add_item(self, sku, quantity, order_id):
        self.items.append({"sku": sku,
                           "quantity": quantity,
                           "deliver_quantity": 0,
                           "order_id": order_id,
                           })

    def adjust_deliver_quantity(self, sku, quantity, order_id):
        if self.is_finalised():
            raise StandardError("Delivery has been finalised, no more adjustments can be made")

        item = self._find_item(sku, order_id)

        if not item:
            raise KeyError("Cannot find specified delivery item")

        if quantity > item["quantity"]:
            raise ValueError("Cannot delivery quantity greater than quantity requested in order")

        item.update({"deliver_quantity": quantity})

    def get_order_descriptors(self):
        orders = {}

        for item in self.items:
            order_id = item["order_id"]
            order_descriptor = {"sku": item["sku"], "quantity": item["deliver_quantity"]}

            if order_id in orders:
                orders[order_id].append(order_descriptor)
            else:
                orders.update({order_id: [order_descriptor]})

        return orders

    def add_invoice(self, invoice_id):
        self.invoice_ids.append(invoice_id)