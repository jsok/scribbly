from domain.shared.entity import  Entity

class BackOrderedItem(Entity):
    """
    A backordered item is created when a product cannot be reserved.
    It tracks which order triggered its creation.
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