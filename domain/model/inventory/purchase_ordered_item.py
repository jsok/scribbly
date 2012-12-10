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