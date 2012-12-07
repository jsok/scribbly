from domain.shared.entity import Entity

class CommittedItem(Entity):
    """
    When an order is placed, it will reserve items from the inventory.
    A reserved item affects on-hand count and will eventually be shipped.
    """
    sku = None
    date = None
    quantity = None
    order_id = None

    def __init__(self, sku, date, quantity, order_id):
        self.sku = sku
        self.date = date
        self.quantity = quantity
        self.order_id = order_id