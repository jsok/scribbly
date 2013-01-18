from datetime import datetime
import operator

from domain.shared.entity import Entity

class InventoryItem(Entity):
    """
    An inventory item is responsible for tracking items of a specific SKU in the following states:
    - on hand: location of each unsold item
    - committed: location of each item which has been committed to a order/sale
    - backorders: item quantity on backorder due to a specific order
    - purchase orders: item quantity awaiting delivery from a purchase order issues to a supplied
    - fulfillments: items which have been sold

    Actions which can be performed on an inventory item:
    - Enter new stock
    - Commit stock for sale
    - Fulfill sale commitment
    - Fulfill backorders -> commit for sale
    - Create purchase order for expected delivery of stock
    """

    def __init__(self, sku, fulfillments=None, purchase_orders=None):
        self.sku = sku

        from domain.model.inventory.tracker import TrackingStateMachine
        from domain.model.inventory.tracker import OnHandState, CommittedState, BackorderState
        self.tracker = TrackingStateMachine()
        self.tracker.add_state(OnHandState("OnHand"))
        self.tracker.add_state(CommittedState("Committed"))
        self.tracker.add_state(BackorderState("Backorder"))

        self.tracker.add_transition("commit", "OnHand", "Committed")
        self.tracker.add_transition("allocate", "OnHand", "Backorder")
        self.tracker.add_transition("fulfill_backorder", "Backorder", "Committed")

        #self.tracker.add_transition("backorder_commitment", "Committed", "Backorder")
        #self.tracker.add_transition("fulfill_commitment", "Committed", "Fulfilled")

        # Some shortcut attributes
        self.on_hand = self.tracker.state("OnHand")
        self.committed = self.tracker.state("Committed")
        self.backorders = self.tracker.state("Backorder")

        self.fulfillments = fulfillments if fulfillments else []
        self.purchase_orders = purchase_orders if purchase_orders else []

    def enter_stock_on_hand(self, quantity, warehouse):
        self.on_hand.track({"quantity": quantity, "warehouse": warehouse})

    def effective_quantity_on_hand(self, warehouse=None):
        return self.on_hand.quantity(warehouse=warehouse)

    def physical_quantity_on_hand(self, warehouse=None):
        physical_quantity = self.on_hand.quantity(warehouse=warehouse)
        committed_quantity = self.committed.quantity(warehouse=warehouse)
        return physical_quantity + committed_quantity

    def find_committed_for_order(self, order_id):
        return self.committed.get(order_id)

    def quantity_committed(self, warehouse=None):
        return self.committed.quantity(warehouse=warehouse)

    def commit(self, quantity, warehouse, order_id):
        # Commit as many items from the specified warehouse as possible
        commit_quantity = min(self.effective_quantity_on_hand(warehouse=warehouse), quantity)

        self.tracker.transition("commit",
            {"quantity": commit_quantity, "warehouse": warehouse},
            {"quantity": commit_quantity, "warehouse": warehouse,
             "order_id": order_id, "date": datetime.now()}
        )()

        # Create a backorder for whatever cannot be committed
        backordered_quantity = max(0, quantity - commit_quantity)

        self.backorders.track({
            "quantity": backordered_quantity,
            "date": datetime.now(),
            "order_id": order_id,
            "allocated": 0}
        )

    def find_backorder_for_order(self, order_id):
        return self.backorders.get(order_id)

    def quantity_backordered(self, order_id=None):
        return self.backorders.quantity(order_id=order_id)

    def fulfill_backorder(self, order_id, quantity, warehouse):
        backorder = self.find_backorder_for_order(order_id)

        # We cannot fulfill the requested quantity
        if backorder is None or \
           quantity > self.quantity_backordered(order_id=order_id) or \
           quantity > self.effective_quantity_on_hand(warehouse=warehouse):
            return

        # XXX: These need to be done atomically

        self.tracker.transition("allocate",
            {"quantity": quantity, "warehouse": warehouse},
            {"quantity": 0, "date": datetime.now(), "order_id": order_id, "allocated": quantity}
        )()

        self.tracker.transition("fulfill_backorder",
            {"quantity": 0, "date": datetime.now(), "order_id": order_id, "allocated": quantity},
            {"quantity": quantity, "warehouse": warehouse, "order_id": order_id, "date": datetime.now()}
        )()
