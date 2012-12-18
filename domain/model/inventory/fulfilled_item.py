from domain.shared.entity import Entity

class FulfilledItem(Entity):
    """
    When an order is fulfilled, a record is kept of which order it
    originated from and which invoice fulfilled it.
    """
    sku = None
    date = None
    quantity = None
    order_id = None
    invoice_id = None

    def __init__(self, sku, date, quantity, order_id, invoice_id):
        self.sku = sku
        self.date = date
        self.quantity = quantity
        self.order_id = order_id
        self.invoice_id = invoice_id