import datetime

from unittest import TestCase, skip
from mock import MagicMock

from domain.model.inventory.inventory_items import *
from domain.model.inventory.inventory_repository import *


class InventoryTestCase(TestCase):

#    def setUp(self):
#        self.repository = InventoryRepository()

#        self.repository.find_by_sku = MagicMock()
#        self.repository.find_by_sku.return_value = InventoryItem(sku="PROD000")

#        self.repository.find_backorders_by_sku = MagicMock()
#        self.repository.find_backorders_by_sku.return_value = [
#            BackOrderedItem(sku="PROD000", date = datetime.datetime.now(), quantity=1, order_id="ORD000"),
#            BackOrderedItem(sku="PROD000", date = datetime.datetime.now(), quantity=2, order_id="ORD001"),
#        ]

#    def test_initialise_with_zero_on_hand(self):
#        item = self.repository.find_by_sku("PROD000")
#        assert item.on_hand == 0


    def test_commit_lt_on_hand(self):
        item = InventoryItem("PROD000", 2)
        item.commit(1, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(1, item.on_hand, "On hand count was not reduced correctly")
        self.assertFalse(committed_items == [], "No items were committed")
        self.assertEqual(1, len(committed_items), "Not exactly one item was committed")
        self.assertEqual(1, committed_items[0].quantity, "Incorrect number of items were committed")
        self.assertEqual("ORD000", committed_items[0].order_id, "Incorrect order ID was set")
        self.assertEquals(1, item.total_committed(), "Only one item should have been committed")

    def test_commit_eq_on_hand(self):
        item = item = InventoryItem("PROD000", 1)
        item.commit(1, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(0, item.on_hand, "On hand count was not reduced correctly")
        self.assertFalse(committed_items == [], "No items were committed")
        self.assertEqual(1, len(committed_items), "Not exactly one item was committed")
        self.assertEqual(1, committed_items[0].quantity, "Incorrect number of items were committed")
        self.assertEqual("ORD000", committed_items[0].order_id, "Incorrect order ID was set")
        self.assertEquals(1, item.total_committed(), "Only one item should have been committed")

    def test_commit_creates_backorder(self):
        item = InventoryItem("PROD000", 1)
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
        item = InventoryItem("PROD000", 0)
        item.backorders.append(BackOrderedItem("PROD000", datetime.datetime.now(), 1, "ORD999"))

        item.commit(1, "ORD000")

        backorders = item.find_backorders("ORD000")
        self.assertFalse(backorders == [], "No items were backordered")
        self.assertEqual(1, len(backorders), "Not exactly one item was backordered")
        self.assertEqual(1, backorders[0].quantity, "Incorrect number of items were backordered")
        self.assertEqual("ORD000", backorders[0].order_id, "Incorrect order ID was set")
        self.assertEquals(0, item.total_committed(), "Items should not have been committed")
        self.assertEquals(2, item.total_backorders(), "Backorder quantity incorrectly calculated")

    def test_fulfil_commitment_exactly(self):
        item = InventoryItem("PROD000", 1)
        item.commit(1, "ORD000")

        item.fulfill_commitment(1, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(0, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(0, item.total_committed(), "No more commitments should remain")

    def test_fulfill_commitment_partially(self):
        item = InventoryItem("PROD000", 3)
        item.commit(2, "ORD000")

        item.fulfill_commitment(1, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(1, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(1, item.total_committed(), "Only one item should remain committed")

    def test_fulfill_multiple_commitments_exactly(self):
        item = InventoryItem("PROD000", 3)
        item.commit(1, "ORD000")
        item.commit(1, "ORD000")

        item.fulfill_commitment(2, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(0, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(0, item.total_committed(), "There should be no more remaining commitments")

    def test_fulfill_multiple_commitments_partially(self):
        item = InventoryItem("PROD000", 4)
        item.commit(2, "ORD000")
        item.commit(2, "ORD000")

        item.fulfill_commitment(3, "ORD000")

        committed_items = item.find_committed("ORD000")

        self.assertEqual(1, len(committed_items), "Item commitment was not fulfilled")
        self.assertEquals(1, item.total_committed(), "Only one item should have been committed")

    def test_fulfill_multiple_order_commitments(self):
        item = InventoryItem("PROD000", 4)
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

    def test_oldest_commitment_fulfilled_first(self):
        item = InventoryItem("PROD000", 4)
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