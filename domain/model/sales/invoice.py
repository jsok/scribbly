import operator

from domain.shared.entity import Entity
from domain.model.sales.line_item import LineItem


class Invoice(Entity):
    def __init__(self, invoice_id, customer, invoice_date, order_id=None, customer_reference=None, line_items=None):
        self.invoice_id = invoice_id
        self.customer = customer
        self.invoice_date = invoice_date
        self.order_id = order_id if order_id else None
        self.customer_reference = customer_reference if customer_reference else None
        self.line_items = line_items if line_items else []
        self.finalised = False

    def tax(self):
        return reduce(operator.add, [i.tax() for i in self.line_items], 0.00)

    def subtotal(self):
        return reduce(operator.add, [i.subtotal() for i in self.line_items], 0.00)

    def total_amount(self):
        return reduce(operator.add, [i.total() for i in self.line_items], 0.00)

    def add_line_item(self, sku, quantity, price, discount, tax_rate=None):
        self.line_items.append(LineItem(sku, quantity, price, discount, tax_rate=tax_rate))
