import datetime
import operator

from domain.shared.entity import Entity

from domain.model.inventory.committed_item import CommittedItem
from domain.model.inventory.backordered_item import BackOrderedItem

class InventoryItem(Entity):
    sku = None
    on_hand = None
    committed = None
    backorders = None

    def __init__(self, sku, on_hand, committed=None, backorders=None):
        self.sku = sku
        self.on_hand = on_hand
        self.committed = committed if committed else []
        self.backorders = backorders if backorders else []

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

    def fulfill_commitment(self, quantity, order_id):
        commitments = self.find_committed(order_id)
        commitments.sort(key=lambda c: c.date, reverse=False)

        total_commitments = reduce(operator.add, [c.quantity for c in commitments])

        if (total_commitments < quantity):
            # We cannot fulfil the requested quantity
            return

        for commitment in commitments:
            if quantity < commitment.quantity:
                commitment.quantity -= quantity
                break
            else:
                quantity -= commitment.quantity
                self.committed.remove(commitment)

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
                    backorder = BackOrderedItem(self.sku, datetime.datetime.now(), commitment.quantity, commitment.order_id)
                    self.backorders.append(backorder)
                    self.committed.remove(commitment)
