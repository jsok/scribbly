from datetime import datetime
import operator

from domain.shared.entity import Entity

from domain.model.inventory.tracker import TrackingStateMachine
from domain.model.inventory.tracker import OnHandState, CommittedState, BackorderState, \
    FulfilledState, PurchaseOrderState, LostAndFoundState

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
    - Track lost & found stock
    """

    def __init__(self, sku, on_hand_buffer=None):
        self.sku = sku

        # Minimum on hand quantity before we need to physically verify stock levels, off by default
        self.on_hand_buffer = on_hand_buffer if on_hand_buffer else 0

        self.tracker = TrackingStateMachine()
        self.tracker.add_state(OnHandState("OnHand"))
        self.tracker.add_state(CommittedState("Committed"))
        self.tracker.add_state(BackorderState("Backorder"))
        self.tracker.add_state(FulfilledState("Fulfilled"))
        self.tracker.add_state(PurchaseOrderState("PurchaseOrder"))
        self.tracker.add_state(LostAndFoundState("Lost"))
        self.tracker.add_state(LostAndFoundState("Found"))

        self.tracker.add_transition("commit", "OnHand", "Committed")
        self.tracker.add_transition("allocate", "OnHand", "Backorder")

        self.tracker.add_transition("fulfill_backorder", "Backorder", "Committed")
        self.tracker.add_transition("cancel_backorder", "Backorder", "OnHand")

        self.tracker.add_action("verify", "Committed")
        self.tracker.add_transition("verify_out_of_stock", "Committed", "Backorder")
        self.tracker.add_transition("backorder_commitment", "Committed", "Backorder")
        self.tracker.add_transition("revert", "Committed", "OnHand")
        self.tracker.add_transition("fulfill", "Committed", "Fulfilled")

        self.tracker.add_transition("delivery", "PurchaseOrder", "OnHand")
        self.tracker.add_action("cancel_purchase_order", "PurchaseOrder")

        self.tracker.add_transition("lost", "OnHand", "Lost")
        self.tracker.add_transition("found", "Found", "OnHand")

        # Some shortcut attributes
        self.on_hand = self.tracker.state("OnHand")
        self.committed = self.tracker.state("Committed")
        self.verification = self.tracker.state("Verify")
        self.backorders = self.tracker.state("Backorder")
        self.fulfilled = self.tracker.state("Fulfilled")
        self.purchase_orders = self.tracker.state("PurchaseOrder")
        self.lost = self.tracker.state("Lost")
        self.found = self.tracker.state("Found")

    # On Hand methods

    def enter_stock_on_hand(self, quantity, warehouse):
        self.on_hand.track({"quantity": quantity, "warehouse": warehouse})

    def effective_quantity_on_hand(self, warehouse=None):
        return self.on_hand.quantity(warehouse=warehouse)

    def physical_quantity_on_hand(self, warehouse=None):
        physical_quantity = self.on_hand.quantity(warehouse=warehouse)
        committed_quantity = self.committed.quantity(warehouse=warehouse)
        return physical_quantity + committed_quantity

    # Commited Items methods

    def find_committed_for_order(self, order_id):
        return self.committed.get(order_id)

    def quantity_committed(self, warehouse=None):
        return self.committed.quantity(warehouse=warehouse)

    def commit(self, quantity, warehouse, order_id):
        effective_quantity = self.effective_quantity_on_hand(warehouse=warehouse)

        # Create a backorder for quantity we know is impossible to commit
        backordered_quantity = max(0, quantity - effective_quantity)
        if backordered_quantity > 0:
            self.backorders.track({"quantity": backordered_quantity, "date": datetime.now(), "order_id": order_id})

        maximum_committable_quantity = quantity - backordered_quantity
        maximum_verified_quantity = max(0, effective_quantity - self.on_hand_buffer)
        verified_quantity = min(maximum_verified_quantity, maximum_committable_quantity)
        unverified_quantity = max(0, maximum_committable_quantity - maximum_verified_quantity)

        self.tracker.transition("commit",
            {"quantity": verified_quantity + unverified_quantity, "warehouse": warehouse},
            {"quantity": verified_quantity, "unverified_quantity": unverified_quantity, "warehouse": warehouse,
             "order_id": order_id, "date": datetime.now()}
        )()

    def fulfill_commitment(self, quantity, warehouse, order_id, invoice_id):
        commitment = self.find_committed_for_order(order_id)
        if not commitment or \
                not commitment.has_key(warehouse) or \
                self.find_fulfillment_for_invoice(invoice_id) is not None:
            return

        self.tracker.transition("fulfill",
            {"quantity": quantity, "warehouse": warehouse, "order_id": order_id, "date": datetime.now()},
            {"quantity": quantity, "order_id": order_id, "invoice_id": invoice_id, "date": datetime.now()},
        )()

    def backorder_commitment(self, quantity, warehouse, order_id):
        commitment = self.find_committed_for_order(order_id)
        if not commitment or warehouse not in commitment or commitment.get(warehouse).quantity < quantity:
            return

        self.tracker.transition("backorder_commitment",
            {"quantity": quantity, "warehouse": warehouse, "order_id": order_id, "date": datetime.now()},
            {"quantity": quantity, "order_id": order_id, "date": datetime.now(), "allocated": 0}
        )()

    def revert(self, quantity, warehouse, order_id):
        commitment = self.find_committed_for_order(order_id)
        if not commitment or warehouse not in commitment or commitment.get(warehouse).quantity < quantity:
            return

        self.tracker.transition("revert",
            {"quantity": quantity, "warehouse": warehouse, "order_id": order_id, "date": datetime.now()},
            {"quantity": quantity, "warehouse": warehouse}
        )()

    def verify_stock_level(self, quantity, warehouse):
        expected_quantity = self.physical_quantity_on_hand(warehouse=warehouse)
        now = datetime.now()

        # Verify the quantity which was physically counted
        self.tracker.action("verify", {"quantity": quantity, "warehouse": warehouse})()

        # Propagate any lost stock into backorders
        if quantity < expected_quantity:
            for item in self.committed.get_unverified(warehouse):
                self.tracker.transition("verify_out_of_stock",
                    {"quantity": item.unverified_quantity, "warehouse": warehouse, "order_id": item.order_id,
                        "date": now},
                    {"quantity": item.unverified_quantity, "warehouse": warehouse, "order_id": item.order_id,
                        "date": now}
                )()

            # Declare lost quantity
            lost_quantity = expected_quantity - quantity
            self.lost_stock(lost_quantity, warehouse)

        elif expected_quantity < quantity:
            found_quantity = quantity - expected_quantity
            self.found_stock(found_quantity, warehouse)


    # Backorder methods

    def find_backorder_for_order(self, order_id):
        return self.backorders.get(order_id)

    def quantity_backordered(self, order_id=None):
        return self.backorders.quantity(order_id=order_id)

    def fulfill_backorder(self, quantity, warehouse, order_id):
        backorder = self.find_backorder_for_order(order_id)

        # We cannot fulfill the requested quantity
        if backorder is None or \
           quantity > self.quantity_backordered(order_id=order_id) or \
           quantity > self.effective_quantity_on_hand(warehouse=warehouse):
            return

        self.tracker.transition("allocate",
            {"quantity": quantity, "warehouse": warehouse},
            {"quantity": 0, "date": datetime.now(), "order_id": order_id, "allocated": quantity}
        )()

        self.tracker.transition("fulfill_backorder",
            {"quantity": 0, "date": datetime.now(), "order_id": order_id, "allocated": quantity},
            {"quantity": quantity, "warehouse": warehouse, "order_id": order_id, "date": datetime.now()}
        )()

    def cancel_backorder(self, warehouse, order_id):
        backorder = self.find_backorder_for_order(order_id)
        if backorder is None:
            return

        # Cancel the entire backorder and return any allocated stock to OnHand
        self.tracker.transition("cancel_backorder",
            {"quantity": 0, "date": datetime.now(), "order_id": order_id, "allocated": 0},
            {"quantity": backorder.allocated, "warehouse": warehouse}
        )()

    # Fulfilled item methods

    def find_fulfillment_for_invoice(self, invoice_id):
        return self.fulfilled.get(invoice_id=invoice_id)

    def quantity_fulfilled(self, invoice_id=None):
        return self.fulfilled.quantity(invoice_id=invoice_id)

    # Purchase order methods

    def find_purchase_order(self, purchase_order_id):
        return self.purchase_orders.get(purchase_order_id)

    def quantity_purchased(self, purchase_order_id=None):
        return self.purchase_orders.quantity(purchase_order_id=purchase_order_id)

    def purchase_item(self, quantity, purchase_order_id, eta_date=None):

        self.purchase_orders.track({
            "quantity": quantity,
            "purchase_order_id": purchase_order_id,
            "date": datetime.now(),
            "eta_date": eta_date if eta_date else None,
         })

    def deliver_purchase_order(self, quantity, warehouse, purchase_order_id):
        po = self.find_purchase_order(purchase_order_id)
        if po is None:
            return

        self.tracker.transition("delivery",
            {"quantity": quantity, "purchase_order_id": purchase_order_id, "date": datetime.now()},
            {"quantity": quantity, "warehouse": warehouse}
        )()

    def cancel_purchase_order(self, purchase_order_id):
        self.tracker.action("cancel_purchase_order", {"purchase_order_id": purchase_order_id})()

    # Lost and Found methods

    def quantity_lost(self, warehouse=None):
        return self.lost.quantity(warehouse=warehouse)

    def quantity_found(self, warehouse=None):
        return self.found.quantity(warehouse=warehouse)

    def lost_stock(self, quantity, warehouse):
        self.tracker.transition("lost",
            {"quantity": quantity, "warehouse": warehouse},
            {"quantity": quantity, "warehouse": warehouse, "date": datetime.now()}
        )()

    def found_stock(self, quantity, warehouse):
        self.tracker.transition("found",
            {"quantity": quantity, "warehouse": warehouse, "date": datetime.now()},
            {"quantity": quantity, "warehouse": warehouse}
        )()