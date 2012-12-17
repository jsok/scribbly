from domain.shared.entity import Entity

class PurchaseOrderedItem(Entity):
    """
    Purchase orders to a supplier create purchase ordered items.
    These items are pending and will be added to on hand stock.
    They optionally have a ETA for availability.
    """
    sku = None
    date = None
    quantity = None
    purchase_order_id = None
    eta_date = None

    def __init__(self, sku, date, quantity, purchase_order_id, eta_date=None):
        self.sku = sku
        self.date = date
        self.quantity = quantity
        self.purchase_order_id = purchase_order_id
        self.eta_date = eta_date if eta_date else None