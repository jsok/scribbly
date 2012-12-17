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