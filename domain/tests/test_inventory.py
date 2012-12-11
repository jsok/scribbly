import datetime

from unittest import TestCase, skip

from factories.inventory import InventoryItemFactory, BackorderFactory, CommitmentFactory, PurchaseOrderFactory
from domain.model.inventory.inventory_items import *


class InventoryTestCase(TestCase):

    def test_commit_lt_on_hand(self):
        item = InventoryItemFactory.build(on_hand=2)
        item.commit(1, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(1, item.on_hand, "On hand count was not reduced correctly")
        self.assertFalse(committed_items == [], "No items were committed")
        self.assertEqual(1, len(committed_items), "Not exactly one item was committed")
        self.assertEqual(1, committed_items[0].quantity, "Incorrect number of items were committed")
        self.assertEqual("ORD000", committed_items[0].order_id, "Incorrect order ID was set")
        self.assertEquals(1, item.total_committed(), "Only one item should have been committed")

    def test_commit_eq_on_hand(self):
        item = InventoryItemFactory.build(on_hand=1)
        item.commit(1, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(0, item.on_hand, "On hand count was not reduced correctly")
        self.assertFalse(committed_items == [], "No items were committed")
        self.assertEqual(1, len(committed_items), "Not exactly one item was committed")
        self.assertEqual(1, committed_items[0].quantity, "Incorrect number of items were committed")
        self.assertEqual("ORD000", committed_items[0].order_id, "Incorrect order ID was set")
        self.assertEquals(1, item.total_committed(), "Only one item should have been committed")

    def test_commit_creates_backorder(self):
        item = InventoryItemFactory.build(on_hand=1)
        item.commit(2, "ORD000")

        committed_items = item.find_committed("ORD000")
        backorders = item.find_backorders("ORD000")

        self.assertEqual(0, item.on_hand, "On hand count was not reduced correctly")

        self.assertFalse(committed_items == [], "No items were committed")
        self.assertEqual(1, len(committed_items), "Not exactly one item was committed")
        self.assertEqual(1, committed_items[0].quantity, "Incorrect number of items were committed")
        self.assertEqual("ORD000", committed_items[0].order_id, "Incorrect order ID was set")
        self.assertEquals(1, item.total_committed(), "Only one item should have been committed")

        self.assertFalse(backorders == [], "No items were backordered")
        self.assertEqual(1, len(backorders), "Not exactly one item was backordered")
        self.assertEqual(1, backorders[0].quantity, "Incorrect number of items were backordered")
        self.assertEqual("ORD000", backorders[0].order_id, "Incorrect order ID was set")
        self.assertEquals(1, item.total_backorders(), "Backorder quantity incorrectly calculated")

    def test_commit_creates_additional_backorder(self):
        existing_backorder = BackorderFactory.build(sku="PROD000", order_id="ORD999")
        item = InventoryItemFactory.build(on_hand=0, backorders=[existing_backorder])

        item.commit(1, "ORD000")

        backorders = item.find_backorders("ORD000")
        self.assertFalse(backorders == [], "No items were backordered")
        self.assertEqual(1, len(backorders), "Not exactly one item was backordered")
        self.assertEqual(1, backorders[0].quantity, "Incorrect number of items were backordered")
        self.assertEqual("ORD000", backorders[0].order_id, "Incorrect order ID was set")
        self.assertEquals(0, item.total_committed(), "Items should not have been committed")
        self.assertEquals(2, item.total_backorders(), "Backorder quantity incorrectly calculated")

    def test_fulfil_commitment_exactly(self):
        item = InventoryItemFactory.build(on_hand=1)
        item.commit(1, "ORD000")

        item.fulfill_commitment(1, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(0, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(0, item.total_committed(), "No more commitments should remain")

    def test_fulfill_commitment_partially(self):
        item = InventoryItemFactory.build(on_hand=3)
        item.commit(2, "ORD000")

        item.fulfill_commitment(1, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(1, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(1, item.total_committed(), "Only one item should remain committed")

    def test_fulfill_multiple_commitments_exactly(self):
        item = InventoryItemFactory.build(on_hand=3)
        item.commit(1, "ORD000")
        item.commit(1, "ORD000")

        item.fulfill_commitment(2, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(0, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(0, item.total_committed(), "There should be no more remaining commitments")

    def test_fulfill_multiple_commitments_partially(self):
        item = InventoryItemFactory.build(on_hand=4)
        item.commit(2, "ORD000")
        item.commit(2, "ORD000")

        item.fulfill_commitment(3, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(1, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(1, item.total_committed(), "Only one item should have been committed")

    def test_fulfill_multiple_order_commitments(self):
        item = InventoryItemFactory.build(on_hand=4)
        item.commit(2, "ORD000")
        item.commit(2, "ORD001")

        item.fulfill_commitment(2, "ORD000")
        item.fulfill_commitment(2, "ORD001")

        committed_items = item.find_committed("ORD000")
        self.assertEqual(0, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(0, item.total_committed(), "There should be no more remaining commitments")

        committed_items = item.find_committed("ORD001")
        self.assertEqual(0, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(0, item.total_committed(), "There should be no more remaining commitments")

    def test_cannot_fulfill_commitment(self):
        item = InventoryItemFactory.build(on_hand=1)
        item.commit(2, "ORD000")

        committed_items = item.find_committed("ORD000")
        self.assertEqual(1, len(committed_items), "Items were not committed")

        item.fulfill_commitment(3, "ORD000")

        committed_items = item.find_committed("ORD000")
        self.assertEqual(1, len(committed_items), "Items should not have been fulfilled")

    def test_oldest_commitment_fulfilled_first(self):
        item = InventoryItemFactory.build(on_hand=4)
        item.commit(3, "ORD000")
        item.commit(1, "ORD000")

        committed_items = item.find_committed("ORD000")
        for commitment in committed_items:
            if commitment.quantity == 3:
                first = commitment
                # Subtract an hour to make the timestamp much older
                first.date = first.date -  datetime.timedelta(hours=1)
            else:
                second = commitment

        item.fulfill_commitment(3, "ORD000")

        committed_items = item.find_committed("ORD000")
        self.assertEqual(1, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(1, item.total_committed(), "Only one item should have been committed")
        self.assertEqual(committed_items[0].date, second.date, "Oldest item was not fulfilled first")

    def test_enter_stock_increases_on_hand(self):
        item = InventoryItemFactory.build(on_hand=0)
        self.assertEquals(0, item.on_hand, "On hand count was not initialised to zero")
        item.enter_stock(1)
        self.assertEquals(1, item.on_hand, "On hand count did not increase")

    def test_remove_stock(self):
        item = InventoryItemFactory.build(on_hand=1)
        item.remove_stock(1)
        self.assertEquals(0, item.on_hand, "On hand count was not decreased")

    def test_remove_stock_gt_on_hand(self):
        item = InventoryItemFactory.build(on_hand=1)
        item.remove_stock(2)
        self.assertEquals(1, item.on_hand, "On hand count should not have decreased")

    def test_remove_stock_with_existing_backorder(self):
        existing_backorder = BackorderFactory.build(sku="PROD000", quantity=1, order_id="ORD000")
        commitment = CommitmentFactory.build(sku="PROD000", quantity=1, order_id="ORD000")
        item = InventoryItemFactory.build(on_hand=0, sku="PROD000",
            backorders=[existing_backorder], committed=[commitment])

        item.remove_stock(1)

        committed_items = item.find_committed("ORD000")
        backordered_items = item.find_backorders("ORD000")

        self.assertEqual(0, item.total_committed(), "Item commitment was not removed")
        self.assertEqual(2, len(backordered_items), "Stock removal did not create backorder")
        self.assertEquals(2, item.total_backorders(), "Wrong backorder quantity set")

    def test_remove_stock_propagates_committed_to_backorder(self):
        commitment = CommitmentFactory.build(sku="PROD000", quantity=1, order_id="ORD000")
        item = InventoryItemFactory.build(on_hand=0, sku="PROD000", committed=[commitment])

        item.remove_stock(1)

        committed_items = item.find_committed("ORD000")
        backordered_items = item.find_backorders("ORD000")

        self.assertEqual(0, len(committed_items), "Item commitment was not removed")
        self.assertEqual(1, len(backordered_items), "Commitment was not converted to backorder")
        self.assertEquals(1, item.total_backorders(), "Wrong backorder quantity set")

    def test_remove_stock_propagates_multiple_partial_committed_to_backorder(self):
        commitment1 = CommitmentFactory.build(sku="PROD000", quantity=1, order_id="ORD000")
        commitment2 = CommitmentFactory.build(sku="PROD000", quantity=3, order_id="ORD001")
        item = InventoryItemFactory.build(on_hand=0, sku="PROD000",
            committed=[commitment1, commitment2])

        item.remove_stock(2)

        self.assertEqual(2, item.total_committed(), "Item commitment was not removed")
        self.assertEqual(1, len(item.find_backorders("ORD000")), "Commitment was not converted to backorder")
        self.assertEqual(1, len(item.find_backorders("ORD001")), "Commitment was not converted to backorder")
        self.assertEquals(2, item.total_backorders(), "Wrong backorder quantity set")

    def test_add_purchase_order(self):
        item = InventoryItemFactory.build(sku="PROD000", on_hand=1)

        po = PurchaseOrderFactory.build(sku="PROD000", quantity=1, purchase_order_id="PO000")
        item.add_purchase_order(po)

        self.assertEquals(1, len(item.purchase_orders), "PO was not added")
        self.assertEqual(po, item.find_purchase_order("PO000"), "Could not find purchase order")

    def test_fulfill_purchase_order(self):
        po = PurchaseOrderFactory.build(sku="PROD000", quantity=1, purchase_order_id="PO000")
        item = InventoryItemFactory.build(sku="PROD000", on_hand=0, purchase_orders=[po])

        item.fulfill_purchase_order("PO000")

        self.assertEquals(1, item.on_hand, "On hand quantity was not increased")
        self.assertIsNone(item.find_purchase_order("PO000"), "Purchase order was not removed after fulfillment")

    def test_fulfill_purchase_order_partially(self):
        po = PurchaseOrderFactory.build(sku="PROD000", quantity=2, purchase_order_id="PO000")
        item = InventoryItemFactory.build(sku="PROD000", on_hand=0, purchase_orders=[po])

        item.fulfill_purchase_order("PO000", quantity=1)
        po = item.find_purchase_order("PO000")

        self.assertEquals(1, item.on_hand, "On hand quantity was not increased")
        self.assertIsNotNone(po, "Purchase order was unable to be found")
        self.assertEquals(1, po.quantity, "Purchase order quantity was not modified")
