import operator

from domain.shared.entity import Entity
from domain.model.sales.line_item import LineItem


class Order(Entity):
    def __init__(self, order_id, customer, order_date, customer_reference=None):
        self.order_id = order_id
        self.customer = customer
        self.order_date = order_date
        self.line_items = []
        self.acknowledgement_date = None
        self.customer_reference = customer_reference if customer_reference else None

    def is_acknowledged(self):
        return self.acknowledgement_date is not None

    def acknowledge(self, date):
        self.acknowledgement_date = date

    def total_amount(self):
        return reduce(operator.add, [i.total() for i in self.line_items], 0.00)

    def add_line_item(self, sku, quantity, price, discount):
        self.line_items.append(LineItem(sku, quantity, price, discount))

    def get_line_items_for_sku(self, sku):
        return [line_item for line_item in self.line_items if line_item.sku == sku]

    def get_order_descriptor(self):
        item_descriptors = []
        for item in self.line_items:
            item_descriptors.append({"sku": item.sku, "quantity": item.quantity})

        return item_descriptors
