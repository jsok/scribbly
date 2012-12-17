import operator

from domain.shared.entity import Entity

class Order(Entity):
    id = None
    order_date = None
    acknowledgement_date = None
    customer_reference = None
    line_items = None

    def __init__(self, id, order_date, line_items=None, acknowledgement_date=None, customer_reference=None):
        self.id = id
        self.order_date = order_date
        self.line_items = line_items if line_items else []
        self.acknowledgement_date = acknowledgement_date if acknowledgement_date else None
        self.customer_reference = customer_reference if customer_reference else None

    def is_acknowledged(self):
        return self.acknowledgement_date != None

    def total_amount(self):
        return reduce(operator.add, [i.amount() for i in self.line_items], 0.00)

    def add_line_item(self, product_id, quantity, price, discount):
        self.line_items.append(self.LineItem(product_id, quantity, price, discount))

    class LineItem():
        """
        Order specific line item.
        """

        product_id = None
        quantity = None
        price = None
        discount = None

        def __init__(self, product_id, quantity, price, discount):
            self.product_id = product_id
            self.quantity = quantity
            self.price = price
            self.discount = discount

        def amount(self):
            return (self.price * (1.0 - self.discount)) * self.quantity