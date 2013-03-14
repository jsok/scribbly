from datetime import datetime
import operator

from domain.shared.entity import Entity

from domain.model.inventory.tracking_state_machine import TrackingStateMachine, TransitionParameter
from domain.model.inventory.tracking_state_machine import OnHandState, CommittedState, BackorderState, \
    FulfilledState, PurchaseOrderState, LostAndFoundState
from domain.model.inventory.tracking_state_machine import TransitionValidationError


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

    def transition(self, *args, **kwargs):
        self.tracker.transition(*args, **kwargs)

    # On Hand methods

    def enter_stock_on_hand(self, quantity):
        try:
            self.on_hand.track({"quantity": quantity})
        except TransitionValidationError:
            return False

        return True

    def effective_quantity_on_hand(self):
        return self.on_hand.quantity()

    def physical_quantity_on_hand(self):
        physical_quantity = self.on_hand.quantity()
        committed_quantity = self.committed.quantity()
        return physical_quantity + committed_quantity

    # Commited Items methods

    def find_committed_for_order(self, order_id):
        return self.committed.get_by_order(order_id)

    def quantity_committed(self):
        return self.committed.quantity()

    def commit(self, quantity, order_id):
        result = True
        effective_quantity = self.effective_quantity_on_hand()

        backordered_quantity = max(0, quantity - effective_quantity)
        if backordered_quantity > 0:
            try:
                # Create a backorder for quantity we know is impossible to commit
                self.backorders.track({"quantity": backordered_quantity, "date": datetime.now(), "order_id": order_id})
            except TransitionValidationError:
                result = False

        # Short circuit, we know we cannot commit anything
        if backordered_quantity == quantity:
            return result

        maximum_committable_quantity = quantity - backordered_quantity
        maximum_verified_quantity = max(0, effective_quantity - self.on_hand_buffer)
        verified_quantity = min(maximum_verified_quantity, maximum_committable_quantity)
        unverified_quantity = max(0, maximum_committable_quantity - maximum_verified_quantity)

        try:
            self.transition("commit",
                            {"quantity": verified_quantity + unverified_quantity},
                            {"quantity": verified_quantity, "unverified_quantity": unverified_quantity,
                             "order_id": order_id, "date": datetime.now()})
        except TransitionValidationError:
            result = False

        return result

    def fulfill_commitment(self, quantity, order_id, invoice_id):
        try:
            now = datetime.now()
            self.transition("fulfill",
                            {"quantity": quantity, "order_id": order_id, "date": now},
                            {"quantity": quantity, "order_id": order_id, "invoice_id": invoice_id, "date": now})
        except TransitionValidationError:
            return False

        return True

    def backorder_commitment(self, quantity, order_id):
        try:
            now = datetime.now()
            self.transition("backorder_commitment",
                            {"quantity": quantity, "order_id": order_id,"date": now},
                            {"quantity": quantity, "order_id": order_id, "date": now, "allocated": 0})
        except TransitionValidationError:
            return False

        return True

    def revert(self, quantity, order_id):
        try:
            now = datetime.now()
            self.transition("revert",
                            {"quantity": quantity, "order_id": order_id, "date": now},
                            {"quantity": quantity})
        except TransitionValidationError:
            return False

        return True

    def needs_stock_verified(self, order_id):
        return not self.committed.is_verified(order_id)

    def verify_stock_level(self, quantity):
        # XXX: Ensure atomicity

        expected_quantity = self.physical_quantity_on_hand()
        now = datetime.now()

        # Verify the quantity which was physically counted
        self.tracker.action("verify", {"quantity": quantity})()

        # Propagate any lost stock into backorders
        if quantity < expected_quantity:
            for item in self.committed.get_unverified():
                self.transition("verify_out_of_stock",
                                {"quantity": item.unverified_quantity, "order_id": item.order_id, "date": now},
                                {"quantity": item.unverified_quantity, "order_id": item.order_id, "date": now})

            # Declare lost quantity
            lost_quantity = expected_quantity - quantity
            self.lost_stock(lost_quantity)

        elif expected_quantity < quantity:
            found_quantity = quantity - expected_quantity
            self.found_stock(found_quantity)

    # Backorder methods

    def find_backorder_for_order(self, order_id):
        return self.backorders.get(order_id)

    def quantity_backordered(self, order_id=None):
        return self.backorders.quantity(order_id=order_id)

    def fulfill_backorder(self, quantity, order_id):
        now = datetime.now()

        try:
            self.transition("allocate",
                            {"quantity": quantity},
                            {"quantity": 0, "date": now, "order_id": order_id, "allocated": quantity})

            self.transition("fulfill_backorder",
                            {"quantity": 0, "date": now, "order_id": order_id, "allocated": quantity},
                            {"quantity": quantity, "order_id": order_id, "date": now})
        except TransitionValidationError:
            return False
        return True

    def cancel_backorder(self, order_id):
        # Cancel the entire backorder and return any allocated stock to OnHand
        try:
            self.transition("cancel_backorder",
                            {"quantity": 0, "date": datetime.now(), "order_id": order_id, "allocated": 0},
                            {"quantity": TransitionParameter("allocated")})
        except TransitionValidationError:
            return False
        return True

    # Fulfilled item methods

    def find_fulfillment_for_invoice(self, invoice_id):
        return self.fulfilled.get(invoice_id)

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

    def deliver_purchase_order(self, quantity, purchase_order_id):
        try:
            self.transition("delivery",
                            {"quantity": quantity, "purchase_order_id": purchase_order_id, "date": datetime.now()},
                            {"quantity": quantity})
        except TransitionValidationError:
            return False
        return True

    def cancel_purchase_order(self, purchase_order_id):
        self.tracker.action("cancel_purchase_order", {"purchase_order_id": purchase_order_id})()

    # Lost and Found methods

    def quantity_lost(self):
        return self.lost.quantity()

    def quantity_found(self):
        return self.found.quantity()

    def lost_stock(self, quantity):
        self.transition("lost",
                        {"quantity": quantity},
                        {"quantity": quantity, "date": datetime.now()})

    def found_stock(self, quantity):
        self.transition("found",
                        {"quantity": quantity, "date": datetime.now()},
                        {"quantity": quantity})