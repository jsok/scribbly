import operator

from domain.shared.entity import Entity
from domain.model.sales.line_item import LineItem

class Invoice(Entity):
    def __init__(self, id, invoice_date, order_id=None, customer_reference=None, line_items=None):
        self.id = id
        self.invoice_date = invoice_date
        self.order_id = order_id if order_id else None
        self.customer_reference = customer_reference if customer_reference else None
        self.line_items = line_items if line_items else []
        self.finalised = False

    def total_amount(self):
        return reduce(operator.add, [i.amount() for i in self.line_items], 0.00)

    def add_line_item(self, sku, quantity, price, discount):
        self.line_items.append(self.InvoiceLineItem(sku, quantity, price, discount))

    class InvoiceLineItem(LineItem):
        """
        Invoice specific line item.
        """
        def __init__(self, sku, quantity, price, discount):
            self.sku = sku
            self.quantity = quantity
            self.price = price
            self.discount = discount

        def amount(self):
            return max(0, (self.price * (1.0 - self.discount)) * self.quantity)