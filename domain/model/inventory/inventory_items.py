import datetime
import operator

from domain.shared.entity import Entity

from domain.model.inventory.committed_item import CommittedItem
from domain.model.inventory.backordered_item import BackOrderedItem
from domain.model.inventory.fulfilled_item import FulfilledItem

class InventoryItem(Entity):
    sku = None
    on_hand = None
    committed = None
    backorders = None
    fulfillments = None
    purchase_orders = None

    def __init__(self, sku, on_hand, committed=None, backorders=None, fulfillments=None, purchase_orders=None):
        self.sku = sku
        self.on_hand = on_hand
        self.committed = committed if committed else []
        self.backorders = backorders if backorders else []
        self.fulfillments = fulfillments if fulfillments else []
        self.purchase_orders = purchase_orders if purchase_orders else []

    def commit(self, quantity, order_id):
        committed_quantity = min(self.on_hand, quantity)
        backordered_quantity = max(0, quantity - self.on_hand)

        self.on_hand -= committed_quantity

        if committed_quantity > 0:
            committed_item = CommittedItem(self.sku, datetime.datetime.now(), committed_quantity, order_id)
            self.committed.append(committed_item)

        if backordered_quantity > 0:
            backorder = BackOrderedItem(self.sku, datetime.datetime.now(), backordered_quantity, order_id)
            self.backorders.append(backorder)

    def find_committed(self, order_id):
        return [i for i in self.committed if i.order_id == order_id]

    def total_committed(self):
        return reduce(operator.add, [c.quantity for c in self.committed], 0)

    def find_backorders(self, order_id):
        return [i for i in self.backorders if i.order_id == order_id]

    def total_backorders(self):
        return reduce(operator.add, [c.quantity for c in self.backorders], 0)

    def find_fulfillment(self, invoice_id):
        return [i for i in self.fulfillments if i.invoice_id == invoice_id]

    def fulfill_commitment(self, quantity, order_id, invoice_id):
        commitments = self.find_committed(order_id)
        commitments.sort(key=lambda c: c.date, reverse=False)

        total_commitments = reduce(operator.add, [c.quantity for c in commitments])

        if (quantity > total_commitments):
            # We cannot fulfil the requested quantity
            return

        for commitment in commitments:
            if quantity < commitment.quantity:
                # Partial fulfillment
                commitment.quantity -= quantity
                fulfillment = FulfilledItem(self.sku, datetime.datetime.now(), quantity, order_id, invoice_id)
                self.fulfillments.append(fulfillment)
                break
            else:
                # Complete fulfillment
                quantity -= commitment.quantity
                fulfillment = FulfilledItem(self.sku, datetime.datetime.now(), commitment.quantity, order_id, invoice_id)
                self.fulfillments.append(fulfillment)
                self.committed.remove(commitment)

            if quantity == 0:
                break

    def enter_stock(self, quantity):
        self.on_hand += quantity

    def remove_stock(self, quantity):
        # Simply reduce on hand count
        if quantity <= self.on_hand:
            self.on_hand -= quantity

        # otherwise we need to convert committed items to backorders
        else:
            commitments = sorted(self.committed, key=lambda c: c.date, reverse=True)

            for commitment in commitments:
                if quantity < commitment.quantity:
                    commitment.quantity -= quantity
                    backorder = BackOrderedItem(self.sku, datetime.datetime.now(), quantity, commitment.order_id)
                    self.backorders.append(backorder)
                    break
                else:
                    quantity -= commitment.quantity
                    backorder = BackOrderedItem(self.sku, datetime.datetime.now(), commitment.quantity,
                        commitment.order_id)
                    self.backorders.append(backorder)
                    self.committed.remove(commitment)

    def find_purchase_order(self, purchase_order_id):
        po = [po for po in self.purchase_orders if po.purchase_order_id == purchase_order_id]
        return po[0] if po else None

    def add_purchase_order(self, po):
        self.purchase_orders.append(po)

    def fulfill_purchase_order(self, purchase_order_id, quantity=None):
        po = self.find_purchase_order(purchase_order_id)
        if po is None:
            return

        if quantity in [None, po.quantity]:
            quantity = po.quantity
            self.purchase_orders.remove(po)
        else:
            po.quantity -= quantity

        self.on_hand += quantity