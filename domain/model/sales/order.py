import operator

from domain.shared.entity import Entity
from domain.model.sales.line_item import LineItem

class Order(Entity):
    def __init__(self, id, order_date, line_items=None, acknowledgement_date=None, customer_reference=None):
        self.id = id
        self.order_date = order_date
        self.line_items = line_items if line_items else []
        self.acknowledgement_date = acknowledgement_date if acknowledgement_date else None
        self.customer_reference = customer_reference if customer_reference else None

    def is_acknowledged(self):
        return self.acknowledgement_date is not None

    def total_amount(self):
        return reduce(operator.add, [i.amount() for i in self.line_items], 0.00)

    def add_line_item(self, sku, quantity, price, discount):
        self.line_items.append(self.OrderLineItem(sku, quantity, price, discount))

    class OrderLineItem(LineItem):
        """
        Order specific line item.
        """
        def __init__(self, sku, quantity, price, discount):
            self.sku = sku
            self.quantity = quantity
            self.price = price
            self.discount = discount

        def amount(self):
            return max(0, (self.price * (1.0 - self.discount)) * self.quantity)